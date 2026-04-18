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
from python.common.runtime_store import RuntimeStore
from python.common.runtime_time import utc_now_iso

# ---------- app bootstrap ----------
# Keep one store per process because the local proof path only needs one sqlite boundary.
store = RuntimeStore()
tracer = init_tracing("synaweave-api")
app = FastAPI(title="SynaWeave Sprint 1 API", version="0.1.0")

# Keep browser access open for the local proof path across web and extension shells.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
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
    surface: str = Field(pattern="^(web|extension|api|ingest)$")
    name: str = Field(min_length=2)
    status: str = Field(pattern="^(ok|error)$")
    durationMs: float = Field(ge=0)
    traceId: str = Field(min_length=6)
    costMicros: int = Field(default=0, ge=0)
    detail: str = ""


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


# ---------- telemetry middleware ----------
# Measure every API request so D3 baselines begin at the request-serving boundary itself.
@app.middleware("http")
async def runtime_probe(request: Request, call_next):
    request_id = f"req_{uuid.uuid4().hex[:12]}"
    request.state.request_id = request_id
    started_at = time.perf_counter()
    parent_context = extract_trace_context(dict(request.headers))
    with tracer.start_as_current_span(
        f"{request.method} {request.url.path}",
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
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR))
            raise
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        status = "ok" if response.status_code < 400 else "error"
        span.set_attribute("http.status_code", response.status_code)
        if status == "error":
            span.set_status(Status(StatusCode.ERROR))
        store.emit_telemetry(
            surface="api",
            name=f"{request.method} {request.url.path}",
            status=status,
            duration_ms=duration_ms,
            trace_id=request.state.trace_id,
            detail=request.url.path,
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
    return JSONResponse(status_code=status_code, content=ok(request, payload, status=state))


# ---------- auth routes ----------
# Keep sign-in email-shaped because Sprint 1 only needs one browser-safe identity proof.
@app.post("/v1/auth/link")
def auth_link(request: Request, body: AuthLinkBody) -> dict[str, Any]:
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
    return ok(request, action)


# ---------- job routes ----------
# Keep job creation and execution explicit so the first background boundary stays visible.
@app.post("/v1/jobs/workspace")
def workspace_job(
    request: Request,
    body: JobBody,
    authorization: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict[str, Any]:
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
    if body.waitForFinish:
        carrier = inject_current_trace_headers()
        subprocess.run(
            [sys.executable, "-m", "apps.ingest.main", "--job-id", job["job_id"]],
            check=True,
            env={
                **os.environ,
                "TRACEPARENT": carrier.get("traceparent", ""),
                "TRACESTATE": carrier.get("tracestate", ""),
            },
        )
        job = store.job_view(job["job_id"], user_id=user_id)
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
# Keep client telemetry explicit so web and extension surfaces can contribute now.
@app.post("/v1/telemetry/emit")
def telemetry_emit(request: Request, body: TelemetryBody) -> dict[str, Any]:
    event = store.emit_telemetry(
        surface=body.surface,
        name=body.name,
        status=body.status,
        duration_ms=body.durationMs,
        trace_id=body.traceId,
        cost_micros=body.costMicros,
        detail=body.detail,
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
