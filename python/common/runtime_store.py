"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  own the first sqlite-backed runtime path for auth workspace jobs and telemetry

- Later Extension Points:
    --> swap the local sqlite proof store only when cloud-backed operational truth becomes durable

- Role:
    --> initializes local runtime tables for the first governed product path
    --> exposes auth workspace job telemetry and baseline helpers used by API ingest and tests

- Exports:
    --> `RuntimeStore`

- Consumed By:
    --> API routes ingest job execution and runtime tests proving the Sprint 1 D2 and D3 slice
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import json
import os
import sqlite3
import statistics
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from python.common.runtime_auth import make_bridge_code, make_token, normalize_email
from python.common.runtime_paths import (
    backend_log_path,
    baseline_path,
    db_path,
    measurements_history_path,
    metrics_path,
    runtime_dir,
    trace_path,
)
from python.common.runtime_time import utc_now_iso


class JobExecutionError(RuntimeError):
    def __init__(self, job_id: str, summary: str, error_detail: str) -> None:
        super().__init__(summary)
        self.job_id = job_id
        self.summary = summary
        self.error_detail = error_detail


# ---------- sqlite helpers ----------
# Keep rows dictionary-shaped so API handlers and tests can read them without positional drift.
def _dict_factory(cursor: sqlite3.Cursor, row: sqlite3.Row) -> dict[str, Any]:
    return {description[0]: row[index] for index, description in enumerate(cursor.description)}


# ---------- connection context ----------
# Keep connection lifecycle centralized so store operations commit and close predictably.
@contextmanager
def _managed_connection(database_path: Path):
    connection = sqlite3.connect(database_path)
    connection.row_factory = _dict_factory
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


# ---------- runtime store ----------
# Keep the local store class narrow so Sprint 1 can prove one truthful runtime path.
class RuntimeStore:
    def __init__(self, database_path: Path | None = None) -> None:
        self.database_path = database_path or db_path()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._recover_database_if_needed()
        self._init_db()

    # ---------- managed session ----------
    # Keep one helper for commit-and-close behavior across store methods.
    @contextmanager
    def _session(self):
        self._recover_database_if_needed()
        self._init_db()
        with _managed_connection(self.database_path) as connection:
            yield connection

    def _recover_database_if_needed(self) -> None:
        if not self.database_path.exists():
            return
        try:
            with sqlite3.connect(self.database_path) as connection:
                result = connection.execute("pragma quick_check").fetchone()
        except sqlite3.DatabaseError as exc:
            if not self._is_resettable_database_error(exc):
                raise
            self._quarantine_database(reason=str(exc))
            return
        if result is None or result[0] != "ok":
            detail = "missing quick_check result" if result is None else f"quick_check={result[0]}"
            self._quarantine_database(reason=detail)

    def _is_resettable_database_error(self, exc: sqlite3.DatabaseError) -> bool:
        detail = str(exc).lower()
        return "malformed" in detail or "not a database" in detail

    def _quarantine_dir(self) -> Path:
        path = self.database_path.parent / "quarantine"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _recovery_log_path(self) -> Path:
        return self.database_path.parent / "runtime-db-recovery.jsonl"

    def _quarantine_database(self, *, reason: str) -> dict[str, Any]:
        recovery = {
            "ts": utc_now_iso(),
            "database_path": str(self.database_path),
            "reason": reason,
        }
        quarantined_path = self._quarantine_dir() / (
            f"{self.database_path.name}.corrupt-{uuid.uuid4().hex[:12]}"
        )
        self.database_path.replace(quarantined_path)
        recovery["quarantined_path"] = str(quarantined_path)
        with self._recovery_log_path().open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(recovery, sort_keys=True) + "\n")
        return recovery

    def _latest_recovery(self) -> dict[str, Any] | None:
        recovery_log = self._recovery_log_path()
        if not recovery_log.exists():
            return None
        latest: dict[str, Any] | None = None
        for line in recovery_log.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            latest = json.loads(line)
        return latest

    def _recovery_event_total(self) -> int:
        recovery_log = self._recovery_log_path()
        if not recovery_log.exists():
            return 0
        return len([line for line in recovery_log.read_text(encoding="utf-8").splitlines() if line])

    # ---------- schema ----------
    # Keep schema creation idempotent so local boot and tests can initialize safely.
    def _init_db(self) -> None:
        schema_text = "\n".join(
            [
                "create table if not exists users (",
                "    user_id text primary key,",
                "    email text not null unique,",
                "    bridge_code text not null,",
                "    created_at text not null",
                ");",
                "",
                "create table if not exists sessions (",
                "    token text primary key,",
                "    user_id text not null,",
                "    surface text not null,",
                "    created_at text not null,",
                "    expires_at text not null,",
                "    foreign key (user_id) references users(user_id)",
                ");",
                "",
                "create table if not exists workspaces (",
                "    workspace_id text primary key,",
                "    user_id text not null unique,",
                "    title text not null,",
                "    last_digest text not null,",
                "    updated_at text not null,",
                "    foreign key (user_id) references users(user_id)",
                ");",
                "",
                "create table if not exists actions (",
                "    action_id text primary key,",
                "    workspace_id text not null,",
                "    user_id text not null,",
                "    kind text not null,",
                "    value text not null,",
                "    source text not null,",
                "    created_at text not null,",
                "    foreign key (workspace_id) references workspaces(workspace_id),",
                "    foreign key (user_id) references users(user_id)",
                ");",
                "",
                "create table if not exists jobs (",
                "    job_id text primary key,",
                "    workspace_id text not null,",
                "    user_id text not null,",
                "    state text not null,",
                "    idempotency_key text not null unique,",
                "    summary text not null,",
                "    created_at text not null,",
                "    finished_at text,",
                "    foreign key (workspace_id) references workspaces(workspace_id),",
                "    foreign key (user_id) references users(user_id)",
                ");",
                "",
                "create table if not exists evals (",
                "    eval_id text primary key,",
                "    workspace_id text not null,",
                "    flow text not null,",
                "    score real not null,",
                "    cost_micros integer not null,",
                "    label text not null,",
                "    created_at text not null,",
                "    foreign key (workspace_id) references workspaces(workspace_id)",
                ");",
                "",
                "create table if not exists telemetry (",
                "    event_id text primary key,",
                "    trace_id text not null,",
                "    surface text not null,",
                "    name text not null,",
                "    status text not null,",
                "    duration_ms real not null,",
                "    cost_micros integer not null,",
                "    detail text not null,",
                "    created_at text not null",
                ");",
            ]
        )
        with _managed_connection(self.database_path) as connection:
            connection.executescript(schema_text)
            self._ensure_column(connection, "jobs", "error_detail", "text not null default ''")
            self._ensure_column(connection, "jobs", "retry_count", "integer not null default 0")

    def _ensure_column(
        self,
        connection: sqlite3.Connection,
        table_name: str,
        column_name: str,
        column_sql: str,
    ) -> None:
        columns = connection.execute(f"pragma table_info({table_name})").fetchall()
        if any(column["name"] == column_name for column in columns):
            return
        connection.execute(f"alter table {table_name} add column {column_name} {column_sql}")

    # ---------- readiness ----------
    # Keep readiness explicit so operators can distinguish startup from missing runtime state.
    def readiness_status(self) -> dict[str, Any]:
        errors: list[str] = []
        db_ready = False
        telemetry_ready = False
        state_dir = runtime_dir()
        latest_recovery = self._latest_recovery()

        try:
            with self._session() as connection:
                connection.execute("select 1").fetchone()
            db_ready = True
        except sqlite3.Error as exc:
            errors.append(f"db:{exc}")

        try:
            state_dir.mkdir(parents=True, exist_ok=True)
            if not os.access(state_dir, os.W_OK):
                raise PermissionError(f"runtime dir is not writable: {state_dir}")
            telemetry_ready = True
        except OSError as exc:
            errors.append(f"telemetry:{exc}")

        return {
            "dbReady": db_ready,
            "telemetryReady": telemetry_ready,
            "runtimeDir": str(state_dir),
            "errors": errors,
            "recoveryEventTotal": self._recovery_event_total(),
            "recoveryLog": str(self._recovery_log_path()),
            "latestRecovery": latest_recovery,
        }

    # ---------- auth ----------
    # Keep auth flows user-scoped and deterministic across web and extension.
    def create_session(self, email: str, surface: str) -> dict[str, Any]:
        normalized_email = normalize_email(email)
        created_at = utc_now_iso()
        expires_at = utc_now_iso()
        user_id = f"usr_{uuid.uuid4().hex[:12]}"
        workspace_id = f"wsp_{uuid.uuid4().hex[:12]}"
        token = make_token()
        bridge_code = make_bridge_code(normalized_email)

        with self._session() as connection:
            existing_user = connection.execute(
                "select * from users where email = ?",
                (normalized_email,),
            ).fetchone()

            if existing_user is None:
                connection.execute(
                    (
                        "insert into users (user_id, email, bridge_code, created_at) "
                        "values (?, ?, ?, ?)"
                    ),
                    (user_id, normalized_email, bridge_code, created_at),
                )
                connection.execute(
                    (
                        "insert into workspaces "
                        "(workspace_id, user_id, title, last_digest, updated_at) "
                        "values (?, ?, ?, ?, ?)"
                    ),
                    (workspace_id, user_id, "SynaWeave Workspace", "", created_at),
                )
                current_user = connection.execute(
                    "select * from users where user_id = ?",
                    (user_id,),
                ).fetchone()
            else:
                current_user = existing_user

            connection.execute(
                (
                    "insert into sessions (token, user_id, surface, created_at, expires_at) "
                    "values (?, ?, ?, ?, ?)"
                ),
                (token, current_user["user_id"], surface, created_at, expires_at),
            )

        identity = self.identity_for_token(token)
        return {
            "token": token,
            "identity": identity,
            "workspace": self.workspace_bootstrap(current_user["user_id"]),
            "bridgeCode": current_user["bridge_code"],
        }

    # ---------- identity ----------
    # Keep identity lookup token-based so browser surfaces never need server-only lookup shortcuts.
    def identity_for_token(self, token: str) -> dict[str, Any]:
        with self._session() as connection:
            session = connection.execute(
                "select * from sessions where token = ?",
                (token,),
            ).fetchone()
            if session is None:
                raise KeyError("unknown session token")
            user = connection.execute(
                "select * from users where user_id = ?",
                (session["user_id"],),
            ).fetchone()
        return {
            "userId": user["user_id"],
            "email": user["email"],
            "bridgeCode": user["bridge_code"],
            "sessionToken": token,
        }

    # ---------- workspace helpers ----------
    # Keep ownership checks centralized so job and action paths enforce the same workspace rules.
    def _workspace_for_user(self, connection: sqlite3.Connection, user_id: str) -> dict[str, Any]:
        workspace = connection.execute(
            "select * from workspaces where user_id = ?",
            (user_id,),
        ).fetchone()
        if workspace is None:
            raise KeyError("unknown workspace")
        return workspace

    def _owned_workspace(
        self, connection: sqlite3.Connection, workspace_id: str, user_id: str
    ) -> dict[str, Any]:
        workspace = connection.execute(
            "select * from workspaces where workspace_id = ?",
            (workspace_id,),
        ).fetchone()
        if workspace is None:
            raise KeyError("unknown workspace")
        if workspace["user_id"] != user_id:
            raise PermissionError("workspace does not belong to session user")
        return workspace

    # ---------- workspace bootstrap ----------
    # Keep bootstrap server-owned so browser surfaces always read durable truth.
    def workspace_bootstrap(self, user_id: str) -> dict[str, Any]:
        with self._session() as connection:
            user = connection.execute(
                "select * from users where user_id = ?",
                (user_id,),
            ).fetchone()
            workspace = self._workspace_for_user(connection, user_id)
            actions = connection.execute(
                "select * from actions where user_id = ? order by created_at desc limit 5",
                (user_id,),
            ).fetchall()
            latest_eval = connection.execute(
                "select * from evals where workspace_id = ? order by created_at desc limit 1",
                (workspace["workspace_id"],),
            ).fetchone()
        return {
            "workspace": {
                "workspaceId": workspace["workspace_id"],
                "title": workspace["title"],
                "email": user["email"],
                "userId": user["user_id"],
                "bridgeCode": user["bridge_code"],
                "lastDigest": workspace["last_digest"],
                "updatedAt": workspace["updated_at"],
            },
            "recentActions": actions,
            "latestEval": latest_eval,
        }

    # ---------- token lookup ----------
    # Keep repeated token-to-user lookup centralized so route code stays thin.
    def user_id_for_token(self, token: str) -> str:
        return self.identity_for_token(token)["userId"]

    def session_surface_for_token(self, token: str) -> str:
        with self._session() as connection:
            session = connection.execute(
                "select surface from sessions where token = ?",
                (token,),
            ).fetchone()
        if session is None:
            raise KeyError("unknown session token")
        return str(session["surface"])

    # ---------- durable action ----------
    # Keep action writes explicit and server-owned so browser-local state
    # never masquerades as truth.
    def record_action(self, token: str, kind: str, value: str, source: str) -> dict[str, Any]:
        user_id = self.user_id_for_token(token)
        session_surface = self.session_surface_for_token(token)
        if session_surface != source:
            raise PermissionError("workspace action source does not match session")
        created_at = utc_now_iso()
        action_id = f"act_{uuid.uuid4().hex[:12]}"
        with self._session() as connection:
            workspace = self._workspace_for_user(connection, user_id)
            connection.execute(
                (
                    "insert into actions "
                    "(action_id, workspace_id, user_id, kind, value, source, created_at) "
                    "values (?, ?, ?, ?, ?, ?, ?)"
                ),
                (
                    action_id,
                    workspace["workspace_id"],
                    user_id,
                    kind,
                    value.strip(),
                    source,
                    created_at,
                ),
            )
            connection.execute(
                "update workspaces set updated_at = ? where workspace_id = ?",
                (created_at, workspace["workspace_id"]),
            )
        return {
            "actionId": action_id,
            "workspaceId": workspace["workspace_id"],
            "userId": user_id,
            "kind": kind,
            "value": value.strip(),
            "source": source,
            "createdAt": created_at,
        }

    # ---------- backend logs ----------
    # Keep backend logs structured and durable so API and ingest correlation survives local replay.
    def record_backend_event(
        self,
        *,
        component: str,
        event: str,
        level: str = "info",
        trace_id: str = "",
        request_id: str = "",
        job_id: str = "",
        workspace_id: str = "",
        user_id: str = "",
        status: str = "",
        detail: str = "",
        fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = {
            "ts": utc_now_iso(),
            "component": component,
            "event": event,
            "level": level,
            "trace_id": trace_id,
            "request_id": request_id,
            "job_id": job_id,
            "workspace_id": workspace_id,
            "user_id": user_id,
            "status": status,
            "detail": detail,
            "fields": fields or {},
        }
        with backend_log_path().open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
        return payload

    # ---------- job queue ----------
    # Keep idempotency explicit so repeated user clicks do not create unbounded duplicate job rows.
    def create_job(self, token: str, workspace_id: str, idempotency_key: str) -> dict[str, Any]:
        user_id = self.user_id_for_token(token)
        created_at = utc_now_iso()
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        with self._session() as connection:
            workspace = self._owned_workspace(connection, workspace_id, user_id)
            existing = connection.execute(
                "select * from jobs where idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
            if existing is not None:
                if (
                    existing["user_id"] != user_id
                    or existing["workspace_id"] != workspace["workspace_id"]
                ):
                    raise PermissionError("job key already belongs to another workspace")
                return existing
            connection.execute(
                (
                    "insert into jobs "
                    "(job_id, workspace_id, user_id, state, idempotency_key, summary, "
                    "created_at, finished_at, error_detail, retry_count) "
                    "values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                ),
                (
                    job_id,
                    workspace["workspace_id"],
                    user_id,
                    "queued",
                    idempotency_key,
                    "Queued for workspace digest generation.",
                    created_at,
                    None,
                    "",
                    0,
                ),
            )
        return self.job_view(job_id, user_id=user_id)

    def mark_job_failed(self, job_id: str, *, summary: str, error_detail: str) -> dict[str, Any]:
        finished_at = utc_now_iso()
        with self._session() as connection:
            job = connection.execute(
                "select * from jobs where job_id = ?",
                (job_id,),
            ).fetchone()
            if job is None:
                raise KeyError("unknown job")
            connection.execute(
                (
                    "update jobs set state = ?, summary = ?, error_detail = ?, "
                    "finished_at = ? where job_id = ?"
                ),
                ("failed", summary, error_detail, finished_at, job_id),
            )
        self.emit_telemetry(
            surface="ingest",
            name="workspace_digest_v1",
            status="error",
            duration_ms=0.0,
            trace_id=f"trc_{job_id}",
            detail=summary,
        )
        return self.job_view(job_id)

    # ---------- job read ----------
    # Keep job reads separate so browser polling stays simple and consistent.
    def job_view(self, job_id: str, user_id: str | None = None) -> dict[str, Any]:
        with self._session() as connection:
            row = connection.execute(
                "select * from jobs where job_id = ?",
                (job_id,),
            ).fetchone()
        if row is None:
            raise KeyError("unknown job")
        if user_id is not None and row["user_id"] != user_id:
            raise PermissionError("job does not belong to session user")
        return row

    # ---------- job execution ----------
    # Keep the first job proof deterministic by summarizing recent actions into one digest.
    def run_job(self, job_id: str) -> dict[str, Any]:
        failure: JobExecutionError | None = None
        eval_row: dict[str, Any] | None = None
        summary = ""
        with self._session() as connection:
            job = connection.execute(
                "select * from jobs where job_id = ?",
                (job_id,),
            ).fetchone()
            if job is None:
                raise KeyError("unknown job")
            if job["state"] == "succeeded":
                return job
            retry_count = job["retry_count"] + 1 if job["state"] == "failed" else job["retry_count"]
            connection.execute(
                (
                    "update jobs set state = ?, summary = ?, finished_at = ?, "
                    "error_detail = ?, retry_count = ? where job_id = ?"
                ),
                (
                    "running",
                    "Running workspace digest generation.",
                    None,
                    "",
                    retry_count,
                    job_id,
                ),
            )
            stage = "digest generation"
            try:
                actions = connection.execute(
                    "select * from actions where workspace_id = ? order by created_at desc limit 5",
                    (job["workspace_id"],),
                ).fetchall()
                summary = self._make_digest(actions)
                stage = "evaluation"
                eval_row = self._write_eval(connection, job["workspace_id"], summary)
                finished_at = utc_now_iso()
                connection.execute(
                    (
                        "update jobs set state = ?, summary = ?, finished_at = ?, "
                        "error_detail = ? where job_id = ?"
                    ),
                    ("succeeded", summary, finished_at, "", job_id),
                )
                connection.execute(
                    "update workspaces set last_digest = ?, updated_at = ? where workspace_id = ?",
                    (summary, finished_at, job["workspace_id"]),
                )
            except Exception as exc:
                error_detail = f"{type(exc).__name__}: {exc}"
                failure_summary = (
                    f"Workspace digest {stage} failed. Check error_detail for more detail."
                )
                finished_at = utc_now_iso()
                connection.execute(
                    (
                        "update jobs set state = ?, summary = ?, error_detail = ?, "
                        "finished_at = ? where job_id = ?"
                    ),
                    ("failed", failure_summary, error_detail, finished_at, job_id),
                )
                failure = JobExecutionError(job_id, failure_summary, error_detail)
        if failure is not None:
            self.emit_telemetry(
                surface="ingest",
                name="workspace_digest_v1",
                status="error",
                duration_ms=0.0,
                trace_id=f"trc_{job_id}",
                detail=failure.summary,
            )
            raise failure
        self.emit_telemetry(
            surface="ingest",
            name="workspace_digest_v1",
            status="ok",
            duration_ms=float(len(summary) + 25),
            trace_id=f"trc_{job_id}",
            cost_micros=0 if eval_row is None else eval_row["cost_micros"],
            detail=summary,
        )
        return self.job_view(job_id)

    # ---------- digest generation ----------
    # Keep the first digest heuristic transparent so later AI upgrades have a baseline.
    def _make_digest(self, actions: list[dict[str, Any]]) -> str:
        if not actions:
            return "No recent actions were available for digest generation."
        fragments = [f"{row['kind']}: {row['value'][:48]}" for row in reversed(actions)]
        return " | ".join(fragments)

    # ---------- eval write ----------
    # Keep evaluation local and cheap so D3 gains one AI-ready score before real inference.
    def _write_eval(
        self, connection: sqlite3.Connection, workspace_id: str, summary: str
    ) -> dict[str, Any]:
        eval_id = f"evl_{uuid.uuid4().hex[:12]}"
        created_at = utc_now_iso()
        score = min(1.0, round(len(summary.strip()) / 120, 3))
        cost_micros = len(summary.encode("utf-8")) * 9
        label = "digest_density"
        connection.execute(
            (
                "insert into evals "
                "(eval_id, workspace_id, flow, score, cost_micros, label, created_at) "
                "values (?, ?, ?, ?, ?, ?, ?)"
            ),
            (eval_id, workspace_id, "workspace_digest_v1", score, cost_micros, label, created_at),
        )
        return {
            "eval_id": eval_id,
            "workspace_id": workspace_id,
            "flow": "workspace_digest_v1",
            "score": score,
            "cost_micros": cost_micros,
            "label": label,
            "created_at": created_at,
        }

    # ---------- telemetry ----------
    # Keep telemetry durable so D3 proof survives local restarts and demos.
    def emit_telemetry(
        self,
        *,
        surface: str,
        name: str,
        status: str,
        duration_ms: float,
        trace_id: str,
        cost_micros: int = 0,
        detail: str = "",
    ) -> dict[str, Any]:
        event = {
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "trace_id": trace_id,
            "surface": surface,
            "name": name,
            "status": status,
            "duration_ms": float(duration_ms),
            "cost_micros": int(cost_micros),
            "detail": detail,
            "created_at": utc_now_iso(),
        }
        with self._session() as connection:
            connection.execute(
                (
                    "insert into telemetry "
                    "(event_id, trace_id, surface, name, status, duration_ms, "
                    "cost_micros, detail, created_at) "
                    "values (?, ?, ?, ?, ?, ?, ?, ?, ?)"
                ),
                tuple(event.values()),
            )
        with trace_path().open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")
        return event

    # ---------- metrics view ----------
    # Keep metrics derived from durable telemetry so local demos and tests can read the same truth.
    def metrics_text(self) -> str:
        snapshot = self.metrics_snapshot()
        lines = [
            f'synaweave_auth_success_total {snapshot["auth_success_total"]}',
            f'synaweave_workspace_action_total {snapshot["workspace_action_total"]}',
            f'synaweave_job_success_total {snapshot["job_success_total"]}',
            f'synaweave_job_failure_total {snapshot["job_failure_total"]}',
            f'synaweave_degraded_event_total {snapshot["degraded_event_total"]}',
            f'synaweave_trace_event_total {snapshot["trace_event_total"]}',
            f'synaweave_api_latency_p95_ms {snapshot["api_latency_p95_ms"]}',
            f'synaweave_job_duration_p95_ms {snapshot["job_duration_p95_ms"]}',
            f'synaweave_workspace_entry_timing_ms {snapshot["workspace_entry_timing_ms"]}',
            f'synaweave_ai_ready_trace_coverage {snapshot["ai_ready_trace_coverage"]}',
            f'synaweave_api_error_total {snapshot["api_error_total"]}',
            f'synaweave_ingest_error_total {snapshot["ingest_error_total"]}',
            f'synaweave_runtime_ready {snapshot["runtime_ready"]}',
            (
                "synaweave_runtime_readiness_error_total "
                f'{snapshot["runtime_readiness_error_total"]}'
            ),
        ]
        metrics_path().write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")
        baseline_path().write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")
        with measurements_history_path().open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(snapshot, sort_keys=True) + "\n")
        return "\n".join(lines) + "\n"

    # ---------- metrics snapshot ----------
    # Keep baseline metrics comparison-ready before a dedicated observability backend exists.
    def metrics_snapshot(self) -> dict[str, Any]:
        readiness = self.readiness_status()
        with self._session() as connection:
            telemetry_rows = connection.execute(
                "select * from telemetry order by created_at asc"
            ).fetchall()
            latest_job = connection.execute(
                "select * from jobs order by coalesce(finished_at, created_at) desc limit 1"
            ).fetchone()
            auth_success_total = connection.execute(
                "select count(*) as count from sessions"
            ).fetchone()["count"]
            workspace_action_total = connection.execute(
                "select count(*) as count from actions"
            ).fetchone()["count"]
            job_success_total = connection.execute(
                "select count(*) as count from jobs where state = 'succeeded'"
            ).fetchone()["count"]
            job_failure_total = connection.execute(
                "select count(*) as count from jobs where state = 'failed'"
            ).fetchone()["count"]
            traced_job_total = connection.execute(
                (
                    "select count(*) as count from jobs "
                    "where state = 'succeeded' "
                    "and exists ("
                    "    select 1 from telemetry "
                    "    where telemetry.surface = 'ingest' "
                    "    and telemetry.trace_id = 'trc_' || jobs.job_id"
                    ")"
                )
            ).fetchone()["count"]
        api_latencies = [row["duration_ms"] for row in telemetry_rows if row["surface"] == "api"]
        job_latencies = [row["duration_ms"] for row in telemetry_rows if row["surface"] == "ingest"]
        workspace_entry_latencies = [
            row["duration_ms"]
            for row in telemetry_rows
            if row["name"] in {"web_workspace_bootstrap", "extension_workspace_bootstrap"}
        ]
        api_error_total = len(
            [row for row in telemetry_rows if row["surface"] == "api" and row["status"] == "error"]
        )
        ingest_error_total = len(
            [
                row
                for row in telemetry_rows
                if row["surface"] == "ingest" and row["status"] == "error"
            ]
        )
        degraded_event_total = len(
            [row for row in telemetry_rows if row["status"] == "degraded"]
        )
        latest_job_id = "" if latest_job is None else latest_job["job_id"]
        latest_job_trace_id = "" if latest_job is None else f"trc_{latest_job_id}"
        return {
            "captured_at": utc_now_iso(),
            "auth_success_total": auth_success_total,
            "workspace_action_total": workspace_action_total,
            "job_success_total": job_success_total,
            "job_failure_total": job_failure_total,
            "trace_event_total": len(telemetry_rows),
            "api_latency_p95_ms": self._p95(api_latencies),
            "job_duration_p95_ms": self._p95(job_latencies),
            "workspace_entry_timing_ms": self._p95(workspace_entry_latencies),
            "ai_ready_trace_coverage": round(
                traced_job_total / job_success_total,
                3,
            )
            if job_success_total
            else 0.0,
            "api_error_total": api_error_total,
            "ingest_error_total": ingest_error_total,
            "degraded_event_total": degraded_event_total,
            "runtime_ready": 1 if readiness["dbReady"] and readiness["telemetryReady"] else 0,
            "runtime_readiness_error_total": len(readiness["errors"]),
            "latest_job_id": latest_job_id,
            "latest_job_state": "" if latest_job is None else latest_job["state"],
            "latest_job_trace_id": latest_job_trace_id,
            "api_hotspots": self._operation_hotspots(telemetry_rows, surface="api"),
            "ingest_hotspots": self._operation_hotspots(telemetry_rows, surface="ingest"),
        }

    def _operation_hotspots(
        self, telemetry_rows: list[dict[str, Any]], *, surface: str
    ) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in telemetry_rows:
            if row["surface"] != surface:
                continue
            grouped.setdefault(row["name"], []).append(row)
        hotspots = [
            {
                "name": name,
                "call_total": len(rows),
                "error_total": len([row for row in rows if row["status"] == "error"]),
                "p95_ms": self._p95([float(row["duration_ms"]) for row in rows]),
            }
            for name, rows in grouped.items()
        ]
        return sorted(
            hotspots,
            key=lambda row: (row["error_total"], row["p95_ms"], row["call_total"]),
            reverse=True,
        )[:3]

    # ---------- p95 helper ----------
    # Keep percentile math dependency-free so the first baseline remains easy to run anywhere.
    def _p95(self, values: list[float]) -> float:
        if not values:
            return 0.0
        if len(values) == 1:
            return round(values[0], 2)
        quantiles = statistics.quantiles(values, n=100, method="inclusive")
        return round(quantiles[94], 2)
