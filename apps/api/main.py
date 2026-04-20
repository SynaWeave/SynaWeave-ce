"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  serve the first runtime path for auth workspace jobs telemetry and metrics

- Later Extension Points:
    --> widen route families only when later bounded domains become durable runtime surfaces

- Role:
    --> exposes liveness readiness auth identity workspace action job telemetry and metrics routes
    --> keeps the first Sprint 1 runtime slice measurable through one FastAPI entrypoint

- Exports:
    --> `app`

- Consumed By:
    --> local operators browser surfaces tests and future runtime startup flows
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import os
import subprocess
import sys
import time
import uuid
from math import isfinite
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from pydantic import BaseModel, Field

from python.common.observability import (
    current_trace_id,
    extract_trace_context,
    init_tracing,
    inject_current_trace_headers,
)
from python.common.runtime_paths import db_path, runtime_dir
from python.common.runtime_store import RuntimeStore
from python.common.runtime_time import utc_now_iso

JOB_WAIT_TIMEOUT_SECONDS = float(os.getenv("SYNAWEAVE_JOB_WAIT_TIMEOUT_SECONDS", "15"))
LOCAL_PROOF_ONLY_AUTH = os.getenv("SYNAWEAVE_LOCAL_PROOF_AUTH", "1") == "1"
LOCAL_PROOF_HOSTS = {"127.0.0.1", "localhost", "testserver"}
MAX_BROWSER_TELEMETRY_DURATION_MS = 300000.0
MAX_BROWSER_TELEMETRY_DETAIL_LENGTH = 160
BROWSER_TELEMETRY_NAMES = {
    "web": {
        "web_action_write",
        "web_digest_run",
        "web_sign_in",
        "web_workspace_bootstrap",
    },
    "extension": {
        "extension_action_write",
        "extension_digest_run",
        "extension_selection_pull",
        "extension_sign_in",
        "extension_workspace_bootstrap",
    },
}

# ---------- app bootstrap ----------
# Keep one store per process because the local proof path only needs one sqlite boundary.
store = RuntimeStore()
tracer = init_tracing("synaweave-api")
app = FastAPI(title="SynaWeave Sprint 1 API", version="0.1.0")

# Keep browser access narrow so the local proof path stays bounded.
# Avoid silently turning local proof into a broad deploy default.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_origin_regex=r"^chrome-extension://[a-z]{32}$",
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "traceparent", "tracestate"],
)


# ---------- request models ----------
# Keep request bodies tiny so the first runtime slice stays versionable and easy to test.
class AuthLinkBody(BaseModel):
    email: str = Field(min_length=3)
    surface: str = Field(pattern="^(web|extension)$")


class WorkspaceActionBody(BaseModel):
    kind: str = Field(pattern="^(capture|note|digest)$")
    value: str = Field(min_length=1)
    source: str = Field(pattern="^(web|extension)$")


class JobBody(BaseModel):
    workspaceId: str = Field(min_length=4)
    waitForFinish: bool = True


class TelemetryBody(BaseModel):
    surface: str = Field(pattern="^(web|extension)$")
    name: str = Field(min_length=2)
    status: str = Field(pattern="^(ok|error|degraded)$")
    durationMs: float = Field(ge=0)
    detail: str = ""


def _sanitize_browser_telemetry_text(value: str, *, max_length: int) -> str:
    compact = " ".join("".join(ch if ch.isprintable() else " " for ch in value).split())
    return compact[:max_length]


def normalize_browser_telemetry(
    body: TelemetryBody,
    *,
    session_surface: str,
    request_trace_id: str,
) -> dict[str, Any]:
    if body.name not in BROWSER_TELEMETRY_NAMES[body.surface]:
        raise HTTPException(status_code=422, detail="telemetry name does not match surface")
    if not isfinite(body.durationMs):
        raise HTTPException(status_code=422, detail="telemetry duration must be finite")
    if session_surface != body.surface:
        raise HTTPException(status_code=403, detail="telemetry surface does not match session")
    return {
        "surface": body.surface,
        "name": body.name,
        "status": body.status,
        "duration_ms": round(min(body.durationMs, MAX_BROWSER_TELEMETRY_DURATION_MS), 2),
        "trace_id": request_trace_id,
        "cost_micros": 0,
        "detail": _sanitize_browser_telemetry_text(
            body.detail,
            max_length=MAX_BROWSER_TELEMETRY_DETAIL_LENGTH,
        ),
    }


# ---------- envelope helpers ----------
# Keep one wrapper so public payloads stay consistent across first-proof endpoints.
def runtime_meta(request: Request) -> dict[str, Any]:
    request_id = request.state.request_id
    return {
        "requestId": request_id,
        "traceId": request.state.trace_id,
        "version": app.version,
        "ts": utc_now_iso(),
    }


def ok(request: Request, payload: dict[str, Any], status: str = "ok") -> dict[str, Any]:
    return {"status": status, "meta": runtime_meta(request), "payload": payload}


def failed_job_response(
    request: Request,
    *,
    job_id: str,
    user_id: str,
    summary: str,
    error_detail: str,
) -> JSONResponse:
    job = store.job_view(job_id, user_id=user_id)
    if job["state"] != "failed":
        job = store.mark_job_failed(job_id, summary=summary, error_detail=error_detail)
    store.record_backend_event(
        component="api",
        event="workspace_job.failed",
        level="error",
        trace_id=request.state.trace_id,
        request_id=request.state.request_id,
        job_id=job["job_id"],
        workspace_id=job["workspace_id"],
        user_id=user_id,
        status=job["state"],
        detail=error_detail,
        fields={"summary": summary},
    )
    return JSONResponse(status_code=502, content=ok(request, job, status="error"))


def retryable_job_response(
    request: Request,
    *,
    job_id: str,
    user_id: str,
    summary: str,
    error_detail: str,
    retry_after_seconds: float,
) -> JSONResponse:
    job = store.job_view(job_id, user_id=user_id)
    if job["state"] != "failed":
        job = store.mark_job_failed(job_id, summary=summary, error_detail=error_detail)
    store.record_backend_event(
        component="api",
        event="workspace_job.timed_out",
        level="warning",
        trace_id=request.state.trace_id,
        request_id=request.state.request_id,
        job_id=job["job_id"],
        workspace_id=job["workspace_id"],
        user_id=user_id,
        status="degraded",
        detail=error_detail,
        fields={
            "summary": summary,
            "retryable": True,
            "retry_after_seconds": retry_after_seconds,
        },
    )
    body = ok(request, job, status="degraded")
    body["detail"] = summary
    body["retryable"] = True
    body["retryAfterSeconds"] = retry_after_seconds
    return JSONResponse(
        status_code=504,
        content=body,
        headers={"Retry-After": str(int(retry_after_seconds))},
    )


def succeeded_job_response(
    request: Request,
    *,
    job: dict[str, Any],
    user_id: str,
) -> dict[str, Any]:
    store.record_backend_event(
        component="api",
        event="workspace_job.completed",
        trace_id=request.state.trace_id,
        request_id=request.state.request_id,
        job_id=job["job_id"],
        workspace_id=job["workspace_id"],
        user_id=user_id,
        status=job["state"],
        detail="job finished before response",
    )
    return ok(request, job, status="ok")


def durable_waited_job_response(
    request: Request,
    *,
    job_id: str,
    user_id: str,
) -> dict[str, Any] | JSONResponse:
    job = store.job_view(job_id, user_id=user_id)
    if job["state"] == "failed":
        return JSONResponse(status_code=502, content=ok(request, job, status="error"))
    return succeeded_job_response(request, job=job, user_id=user_id)


# ---------- auth helpers ----------
# Keep bearer parsing centralized so route handlers stay focused on runtime behavior.
def require_token(authorization: str | None) -> str:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="empty bearer token")
    return token


def require_user_id(authorization: str | None) -> str:
    token = require_token(authorization)
    try:
        return store.user_id_for_token(token)
    except KeyError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def require_authenticated_token(authorization: str | None) -> tuple[str, str]:
    token = require_token(authorization)
    try:
        return token, store.user_id_for_token(token)
    except KeyError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def require_browser_telemetry_surface(authorization: str | None) -> str:
    token = require_token(authorization)
    try:
        return store.session_surface_for_token(token)
    except KeyError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def require_local_proof_request(request: Request) -> None:
    if not LOCAL_PROOF_ONLY_AUTH:
        return
    if request.url.hostname in LOCAL_PROOF_HOSTS:
        return
    raise HTTPException(
        status_code=403,
        detail=(
            "local proof auth bootstrap is restricted to loopback hosts "
            "until a real provider-backed auth boundary is configured"
        ),
    )


# ---------- telemetry middleware ----------
# Measure every API request so D3 baselines begin at the request-serving boundary itself.
@app.middleware("http")
async def runtime_probe(request: Request, call_next):
    request_id = f"req_{uuid.uuid4().hex[:12]}"
    request.state.request_id = request_id
    started_at = time.perf_counter()
    route_name = f"{request.method} {request.url.path}"
    parent_context = extract_trace_context(dict(request.headers))
    with tracer.start_as_current_span(
        route_name,
        context=parent_context,
        kind=trace.SpanKind.SERVER,
    ) as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.route", request.url.path)
        span.set_attribute("synaweave.request_id", request_id)
        request.state.trace_id = current_trace_id()
        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR))
            store.emit_telemetry(
                surface="api",
                name=route_name,
                status="error",
                duration_ms=duration_ms,
                trace_id=request.state.trace_id,
                detail=request.url.path,
            )
            store.record_backend_event(
                component="api",
                event="request.failed",
                level="error",
                trace_id=request.state.trace_id,
                request_id=request_id,
                status="error",
                detail=str(exc),
                fields={
                    "duration_ms": duration_ms,
                    "method": request.method,
                    "path": request.url.path,
                },
            )
            raise
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        status = "ok" if response.status_code < 400 else "error"
        span.set_attribute("http.status_code", response.status_code)
        if status == "error":
            span.set_status(Status(StatusCode.ERROR))
        store.emit_telemetry(
            surface="api",
            name=route_name,
            status=status,
            duration_ms=duration_ms,
            trace_id=request.state.trace_id,
            detail=request.url.path,
        )
        store.record_backend_event(
            component="api",
            event="request.completed",
            level="error" if status == "error" else "info",
            trace_id=request.state.trace_id,
            request_id=request_id,
            status=status,
            detail=request.url.path,
            fields={
                "duration_ms": duration_ms,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
            },
        )
        response.headers["x-request-id"] = request_id
        response.headers["x-trace-id"] = request.state.trace_id
        response.headers.update(inject_current_trace_headers())
        return response


# ---------- health ----------
# Keep liveness and readiness separate so operators can distinguish
# process truth from dependency truth.
@app.get("/health/live")
def live(request: Request) -> dict[str, Any]:
    return ok(request, {"service": "api", "state": "live", "ts": utc_now_iso()})


@app.get("/health/ready")
def ready(request: Request) -> JSONResponse:
    readiness = store.readiness_status()
    state = "ready" if readiness["dbReady"] and readiness["telemetryReady"] else "not_ready"
    payload = {
        "service": "api",
        "state": state,
        "dbReady": readiness["dbReady"],
        "telemetryReady": readiness["telemetryReady"],
        "runtimeDir": readiness["runtimeDir"],
        "errors": readiness["errors"],
        "ts": utc_now_iso(),
    }
    status_code = 200 if state == "ready" else 503
    if status_code != 200:
        store.record_backend_event(
            component="api",
            event="runtime.degraded",
            level="warning",
            trace_id=request.state.trace_id,
            request_id=request.state.request_id,
            status=state,
            detail=",".join(readiness["errors"]),
            fields={"errors": readiness["errors"]},
        )
    return JSONResponse(status_code=status_code, content=ok(request, payload, status=state))


# ---------- auth routes ----------
# Keep sign-in email-shaped because Sprint 1 only needs one browser-safe identity proof.
@app.post("/v1/auth/link")
def auth_link(request: Request, body: AuthLinkBody) -> dict[str, Any]:
    require_local_proof_request(request)
    session = store.create_session(body.email, body.surface)
    return ok(
        request,
        {
            "token": session["token"],
            "identity": session["identity"],
            "workspace": session["workspace"],
            "bridgeCode": session["bridgeCode"],
        },
    )


@app.get("/v1/identity")
def identity(request: Request, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    token = require_token(authorization)
    try:
        payload = store.identity_for_token(token)
    except KeyError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return ok(request, payload)


# ---------- workspace routes ----------
# Keep workspace bootstrap server-owned so both browser surfaces read the same durable truth.
@app.get("/v1/workspace/bootstrap")
def workspace_bootstrap(
    request: Request,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    token = require_token(authorization)
    try:
        user_id = store.user_id_for_token(token)
        payload = store.workspace_bootstrap(user_id)
    except KeyError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return ok(request, payload)


@app.post("/v1/workspace/action")
def workspace_action(
    request: Request,
    body: WorkspaceActionBody,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    token = require_token(authorization)
    try:
        action = store.record_action(token, body.kind, body.value, body.source)
    except KeyError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return ok(request, action)


# ---------- job routes ----------
# Keep job creation and execution explicit so the first background boundary stays visible.
@app.post("/v1/jobs/workspace")
def workspace_job(
    request: Request,
    body: JobBody,
    authorization: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> Any:
    token, user_id = require_authenticated_token(authorization)
    try:
        job = store.create_job(
            token,
            body.workspaceId,
            idempotency_key or f"idem_{uuid.uuid4().hex[:12]}",
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    store.record_backend_event(
        component="api",
        event="workspace_job.queued",
        trace_id=request.state.trace_id,
        request_id=request.state.request_id,
        job_id=job["job_id"],
        workspace_id=job["workspace_id"],
        user_id=user_id,
        status=job["state"],
        detail="job accepted",
        fields={"wait_for_finish": body.waitForFinish},
    )
    if body.waitForFinish:
        if job["state"] in {"queued", "failed"}:
            carrier = inject_current_trace_headers()
            try:
                subprocess.run(
                    [sys.executable, "-m", "apps.ingest.main", "--job-id", job["job_id"]],
                    check=True,
                    timeout=JOB_WAIT_TIMEOUT_SECONDS,
                    env={
                        **os.environ,
                        "TRACEPARENT": carrier.get("traceparent", ""),
                        "TRACESTATE": carrier.get("tracestate", ""),
                        "SYNAWEAVE_RUNTIME_DIR": str(runtime_dir()),
                        "SYNAWEAVE_RUNTIME_DB_PATH": str(db_path()),
                    },
                )
            except subprocess.TimeoutExpired as exc:
                return retryable_job_response(
                    request,
                    job_id=job["job_id"],
                    user_id=user_id,
                    summary=(
                        "Workspace digest timed out before waitForFinish could confirm success. "
                        "The job was marked failed so you can retry safely."
                    ),
                    error_detail=f"{type(exc).__name__}: {exc}",
                    retry_after_seconds=JOB_WAIT_TIMEOUT_SECONDS,
                )
            except subprocess.CalledProcessError as exc:
                job = store.job_view(job["job_id"], user_id=user_id)
                if job["state"] == "succeeded":
                    return succeeded_job_response(request, job=job, user_id=user_id)
                return failed_job_response(
                    request,
                    job_id=job["job_id"],
                    user_id=user_id,
                    summary=(
                        "Workspace digest ingest execution failed. "
                        "Check error_detail for more detail."
                    ),
                    error_detail=f"{type(exc).__name__}: {exc}",
                )
            except OSError as exc:
                job = store.job_view(job["job_id"], user_id=user_id)
                if job["state"] == "succeeded":
                    return succeeded_job_response(request, job=job, user_id=user_id)
                return failed_job_response(
                    request,
                    job_id=job["job_id"],
                    user_id=user_id,
                    summary=(
                        "Workspace digest worker could not start. "
                        "Check error_detail for more detail."
                    ),
                    error_detail=f"{type(exc).__name__}: {exc}",
                )
        return durable_waited_job_response(request, job_id=job["job_id"], user_id=user_id)
    return ok(request, job, status="accepted")


@app.get("/v1/jobs/{job_id}")
def job_view(
    request: Request,
    job_id: str,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    user_id = require_user_id(authorization)
    try:
        payload = store.job_view(job_id, user_id=user_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return ok(request, payload)


# ---------- telemetry route ----------
# Keep browser telemetry explicit while reserving API and ingest surfaces for server-owned truth.
@app.post("/v1/telemetry/emit")
def telemetry_emit(
    request: Request,
    body: TelemetryBody,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    event = store.emit_telemetry(
        **normalize_browser_telemetry(
            body,
            session_surface=require_browser_telemetry_surface(authorization),
            request_trace_id=request.state.trace_id,
        )
    )
    return ok(request, event, status="accepted")


# ---------- metrics ----------
# Keep the metrics endpoint plain so Prometheus and curl can read it without translation.
@app.get("/metrics")
def metrics() -> PlainTextResponse:
    return PlainTextResponse(store.metrics_text())


# ---------- baseline ----------
# Keep one JSON baseline read so humans and scripts can inspect the proof snapshot.
@app.get("/v1/baseline")
def baseline(request: Request) -> dict[str, Any]:
    store.metrics_text()
    payload = store.metrics_snapshot()
    return ok(request, payload)
