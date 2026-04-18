/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  drive the first authenticated web control-plane shell for sign-in workspace bootstrap durable actions and job visibility

- Later Extension Points:
  --> widen the shell only when later workspace routes and richer product domains become durable web concerns

- Role:
  --> handles browser-safe auth bootstrap workspace refresh durable actions and digest job flow
  --> emits web-surface telemetry so the first quality baseline includes client-side runtime proof

- Exports:
  --> web runtime side effects only

- Consumed By:
  --> `apps/web/index.html` during the first local Sprint 1 runtime proof flow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

const API_BASE_URL =
	localStorage.getItem("synaweave.apiBaseUrl") || "http://127.0.0.1:8000";
const TOKEN_KEY = "synaweave.webToken";
const TRACE_PREFIX = "web";
const TRANSIENT_ERROR_MESSAGE =
	"Temporary API or provider failure. Session kept so you can retry.";

const els = {
	authCard: document.getElementById("auth-card"),
	workspaceCard: document.getElementById("workspace-card"),
	degradedCard: document.getElementById("degraded-card"),
	degradedMessage: document.getElementById("degraded-message"),
	retryButton: document.getElementById("retry-button"),
	emailInput: document.getElementById("email-input"),
	signInButton: document.getElementById("sign-in-button"),
	signOutButton: document.getElementById("sign-out-button"),
	identityEmail: document.getElementById("identity-email"),
	bridgeCode: document.getElementById("bridge-code"),
	workspaceId: document.getElementById("workspace-id"),
	actionInput: document.getElementById("action-input"),
	saveActionButton: document.getElementById("save-action-button"),
	runJobButton: document.getElementById("run-job-button"),
	lastDigest: document.getElementById("last-digest"),
	latestEval: document.getElementById("latest-eval"),
	recentActions: document.getElementById("recent-actions"),
	statusLine: document.getElementById("status-line"),
};

const runtimeState = {
	retryAction: null,
	retryLabel: "",
};

void refreshRuntime();

els.retryButton.addEventListener("click", async () => {
	if (!runtimeState.retryAction) {
		setStatus("No retryable web request is waiting right now.");
		return;
	}
	setStatus(`Retrying ${runtimeState.retryLabel}.`);
	await runtimeState.retryAction();
});

els.signInButton.addEventListener("click", async () => {
	const email = String(els.emailInput.value || "").trim();
	if (!email) {
		setStatus("Enter an email before signing in.");
		return;
	}

	const startedAt = performance.now();
	const response = await fetchJson("/v1/auth/link", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ email, surface: "web" }),
	});
	localStorage.setItem(TOKEN_KEY, response.payload.token);
	clearDegradedState();
	await emitTelemetry("web_sign_in", startedAt, "ok", `email:${email}`);
	await refreshRuntime();
});

els.signOutButton.addEventListener("click", async () => {
	localStorage.removeItem(TOKEN_KEY);
	clearDegradedState();
	showSignedOut();
	setStatus("Signed out of the web shell.");
});

els.saveActionButton.addEventListener("click", async () => {
	const value = String(els.actionInput.value || "").trim();
	if (!value) {
		setStatus("Write a note before sending the durable action.");
		return;
	}
	const startedAt = performance.now();
	try {
		await authedFetchJson("/v1/workspace/action", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ kind: "note", value, source: "web" }),
		});
	} catch (error) {
		const outcome = await handleRuntimeFailure(
			"web_action_write",
			startedAt,
			error,
			"the durable action write",
			async () => {
				await els.saveActionButton.click();
			},
		);
		if (outcome.handled) {
			return;
		}
		throw error;
	}
	await emitTelemetry("web_action_write", startedAt, "ok", value.slice(0, 24));
	clearDegradedState();
	els.actionInput.value = "";
	await refreshRuntime();
	setStatus("Durable action written through the API.");
});

els.runJobButton.addEventListener("click", async () => {
	const workspaceId = els.workspaceId.textContent || "";
	if (!workspaceId || workspaceId === "—") {
		setStatus("No workspace is ready yet.");
		return;
	}
	const startedAt = performance.now();
	try {
		await authedFetchJson("/v1/jobs/workspace", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"Idempotency-Key": `web-${Date.now()}`,
			},
			body: JSON.stringify({ workspaceId, waitForFinish: true }),
		});
	} catch (error) {
		const outcome = await handleRuntimeFailure(
			"web_digest_run",
			startedAt,
			error,
			"the digest job",
			async () => {
				await els.runJobButton.click();
			},
		);
		if (outcome.handled) {
			return;
		}
		throw error;
	}
	await emitTelemetry("web_digest_run", startedAt, "ok", workspaceId);
	clearDegradedState();
	await refreshRuntime();
	setStatus("Background digest completed and reloaded.");
});

async function refreshRuntime() {
	const token = localStorage.getItem(TOKEN_KEY);
	if (!token) {
		clearDegradedState();
		showSignedOut();
		setStatus("No active web session yet.");
		return;
	}

	const startedAt = performance.now();
	try {
		const identity = await authedFetchJson("/v1/identity", { method: "GET" });
		const workspace = await authedFetchJson("/v1/workspace/bootstrap", {
			method: "GET",
		});
		await emitTelemetry(
			"web_workspace_bootstrap",
			startedAt,
			"ok",
			identity.payload.email,
		);
		clearDegradedState();
		showSignedIn(identity.payload, workspace.payload);
		setStatus(`Workspace ready for ${identity.payload.email}.`);
	} catch (error) {
		await handleRuntimeFailure(
			"web_workspace_bootstrap",
			startedAt,
			error,
			"the workspace refresh",
			refreshRuntime,
		);
		return;
	}
}

function showSignedIn(identity, workspacePayload) {
	els.authCard.classList.add("hidden");
	els.workspaceCard.classList.remove("hidden");
	els.identityEmail.textContent = identity.email;
	els.bridgeCode.textContent = identity.bridgeCode;
	els.workspaceId.textContent = workspacePayload.workspace.workspaceId;
	els.lastDigest.textContent =
		workspacePayload.workspace.lastDigest || "No digest yet.";
	els.latestEval.textContent = workspacePayload.latestEval
		? `${workspacePayload.latestEval.label}: ${workspacePayload.latestEval.score}`
		: "No eval yet.";
	renderActions(workspacePayload.recentActions || []);
}

function showSignedOut() {
	els.authCard.classList.remove("hidden");
	els.workspaceCard.classList.add("hidden");
	els.identityEmail.textContent = "—";
	els.bridgeCode.textContent = "—";
	els.workspaceId.textContent = "—";
	els.lastDigest.textContent = "—";
	els.latestEval.textContent = "—";
	els.recentActions.innerHTML = "";
}

function showSessionHeld() {
	els.authCard.classList.add("hidden");
	els.workspaceCard.classList.remove("hidden");
}

function renderActions(actions) {
	els.recentActions.innerHTML = "";
	for (const action of actions) {
		const item = document.createElement("li");
		item.textContent = `${action.kind} • ${action.source} • ${action.value}`;
		els.recentActions.appendChild(item);
	}
}

async function fetchJson(path, init) {
	let response;
	try {
		response = await fetch(`${API_BASE_URL}${path}`, {
			...init,
			headers: {
				...(init?.headers || {}),
				...makeTraceHeaders(),
			},
		});
	} catch (error) {
		throw makeRuntimeError({
			kind: "transient",
			retryable: true,
			status: 0,
			message: error instanceof Error ? error.message : String(error),
		});
	}
	if (!response.ok) {
		const detail = await readFailureDetail(response);
		throw makeRuntimeError({
			kind: isAuthFailureStatus(response.status) ? "auth" : "transient",
			retryable: !isAuthFailureStatus(response.status),
			status: response.status,
			message: detail,
		});
	}
	return response.json();
}

async function authedFetchJson(path, init) {
	const token = localStorage.getItem(TOKEN_KEY);
	return fetchJson(path, {
		...init,
		headers: {
			...(init.headers || {}),
			Authorization: `Bearer ${token}`,
		},
	});
}

async function emitTelemetry(name, startedAt, status, detail) {
	const durationMs = Number((performance.now() - startedAt).toFixed(2));
	await fetch(`${API_BASE_URL}/v1/telemetry/emit`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({
			surface: "web",
			name,
			status,
			durationMs,
			traceId: `${TRACE_PREFIX}_${Date.now()}`,
			detail,
		}),
	}).catch(() => null);
}

async function handleRuntimeFailure(
	telemetryName,
	startedAt,
	error,
	retryLabel,
	retryAction,
) {
	const failure = normalizeRuntimeError(error);
	await emitTelemetry(
		telemetryName,
		startedAt,
		failure.kind === "auth" ? "error" : "degraded",
		buildFailureTelemetryDetail(failure),
	);
	if (failure.kind === "auth") {
		localStorage.removeItem(TOKEN_KEY);
		clearDegradedState();
		showSignedOut();
		setStatus(
			"Stored session expired or was invalid, so the web shell returned to signed-out state.",
		);
		return { handled: true, kind: "auth" };
	}
	showSessionHeld();
	setDegradedState(TRANSIENT_ERROR_MESSAGE, retryLabel, retryAction);
	setStatus(`${TRANSIENT_ERROR_MESSAGE}`);
	return { handled: true, kind: "transient" };
}

function setDegradedState(message, retryLabel, retryAction) {
	runtimeState.retryAction = retryAction;
	runtimeState.retryLabel = retryLabel;
	els.degradedMessage.textContent = message;
	els.retryButton.textContent = `Retry ${retryLabel}`;
	els.degradedCard.classList.remove("hidden");
}

function clearDegradedState() {
	runtimeState.retryAction = null;
	runtimeState.retryLabel = "";
	els.degradedCard.classList.add("hidden");
	els.degradedMessage.textContent =
		"A retryable runtime issue is holding the current session.";
	els.retryButton.textContent = "Retry last request";
}

function normalizeRuntimeError(error) {
	if (error && typeof error === "object" && "kind" in error) {
		return error;
	}
	return makeRuntimeError({
		kind: "transient",
		retryable: true,
		status: 0,
		message: error instanceof Error ? error.message : String(error),
	});
}

function makeRuntimeError({ kind, retryable, status, message }) {
	return { kind, retryable, status, message };
}

function buildFailureTelemetryDetail(failure) {
	return [
		`kind=${failure.kind}`,
		`retryable=${String(failure.retryable)}`,
		`status=${failure.status || "network"}`,
		`message=${failure.message}`,
	]
		.join(" ")
		.slice(0, 180);
}

async function readFailureDetail(response) {
	const contentType = response.headers.get("content-type") || "";
	if (contentType.includes("application/json")) {
		const body = await response.json().catch(() => null);
		const detail = body?.detail;
		if (typeof detail === "string" && detail.trim()) {
			return detail.trim();
		}
	}
	const text = await response.text().catch(() => "");
	return text.trim() || `Request failed: ${response.status}`;
}

function isAuthFailureStatus(status) {
	return status === 401 || status === 403;
}

function setStatus(message) {
	els.statusLine.textContent = message;
}

function makeTraceHeaders() {
	const traceId = Array.from(crypto.getRandomValues(new Uint8Array(16)))
		.map((value) => value.toString(16).padStart(2, "0"))
		.join("");
	const spanId = Array.from(crypto.getRandomValues(new Uint8Array(8)))
		.map((value) => value.toString(16).padStart(2, "0"))
		.join("");
	return { traceparent: `00-${traceId}-${spanId}-01` };
}
