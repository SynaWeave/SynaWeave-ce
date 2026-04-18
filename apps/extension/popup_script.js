/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  drive the first authenticated extension side-panel shell for shared identity capture durable actions and digest visibility

- Later Extension Points:
  --> widen the panel only when later capture queues retry logic or richer study widgets become durable extension concerns

- Role:
  --> handles browser-safe auth workspace refresh selection capture durable action writes and digest execution
  --> emits extension-surface telemetry so the D3 proof baseline includes the browser-native client runtime

- Exports:
  --> popup runtime side effects only

- Consumed By:
  --> `apps/extension/popup.html` inside the Manifest V3 side-panel surface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

// ---------- runtime config ----------
// Keep local API targeting explicit so the side-panel proof works without a bundler.
const API_BASE_URL = "http://127.0.0.1:8000";
const TOKEN_KEY = "synaweave.extensionToken";
const PANEL_OPEN_REQUEST_KEY = "synaweave.sidePanelOpenRequestedAt";
const PANEL_RUNTIME_EVIDENCE_KEY = "synaweave.sidePanelRuntimeEvidence";
const TRACE_PREFIX = "ext";
const TRANSIENT_ERROR_MESSAGE =
	"Temporary API or provider failure. Session kept so you can retry.";

// ---------- dom handles ----------
// Keep selectors centralized so state transitions stay easy to review.
const els = {
	authSection: document.getElementById("auth-section"),
	workspaceSection: document.getElementById("workspace-section"),
	degradedCard: document.getElementById("ext-degraded-card"),
	degradedMessage: document.getElementById("ext-degraded-message"),
	retryButton: document.getElementById("ext-retry-button"),
	emailInput: document.getElementById("ext-email-input"),
	signInButton: document.getElementById("ext-sign-in-button"),
	signOutButton: document.getElementById("ext-sign-out-button"),
	identityEmail: document.getElementById("ext-identity-email"),
	bridgeCode: document.getElementById("ext-bridge-code"),
	workspaceId: document.getElementById("ext-workspace-id"),
	actionInput: document.getElementById("ext-action-input"),
	pullSelectionButton: document.getElementById("pull-selection-button"),
	saveActionButton: document.getElementById("save-extension-action-button"),
	runJobButton: document.getElementById("run-extension-job-button"),
	lastDigest: document.getElementById("ext-last-digest"),
	latestEval: document.getElementById("ext-latest-eval"),
	recentActions: document.getElementById("ext-recent-actions"),
	statusLine: document.getElementById("panel-status-line"),
};

const runtimeState = {
	retryAction: null,
	retryLabel: "",
};

// ---------- boot ----------
// Rehydrate any stored token first so panel reopen continuity is part of the runtime proof.
void recordPanelRuntimeEvidence();
void refreshRuntime();

els.retryButton.addEventListener("click", async () => {
	if (!runtimeState.retryAction) {
		setStatus("No retryable extension request is waiting right now.");
		return;
	}
	setStatus(`Retrying ${runtimeState.retryLabel}.`);
	await runtimeState.retryAction();
});

// ---------- auth flow ----------
// Keep sign-in email-driven so the extension mirrors the web identity path.
els.signInButton.addEventListener("click", async () => {
	const email = String(els.emailInput.value || "").trim();
	if (!email) {
		setStatus("Enter the same email used in the web shell.");
		return;
	}
	const startedAt = performance.now();
	const response = await fetchJson("/v1/auth/link", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ email, surface: "extension" }),
	});
	await chrome.storage.local.set({ [TOKEN_KEY]: response.payload.token });
	clearDegradedState();
	await emitTelemetry("extension_sign_in", startedAt, "ok", email);
	await refreshRuntime();
});

els.signOutButton.addEventListener("click", async () => {
	await chrome.storage.local.remove(TOKEN_KEY);
	clearDegradedState();
	showSignedOut();
	setStatus("Signed out of the extension panel.");
});

// ---------- selection and write flow ----------
// Keep capture and durable write actions explicit so the panel proves each runtime step.
els.pullSelectionButton.addEventListener("click", async () => {
	const startedAt = performance.now();
	const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
	if (!tab || typeof tab.id !== "number") {
		setStatus("No active tab was available for selection capture.");
		return;
	}
	const response = await chrome.tabs
		.sendMessage(tab.id, { type: "selection:get" })
		.catch(() => null);
	const text = String(response?.text || "").trim();
	if (!text) {
		setStatus("The active page did not return a selection.");
		return;
	}
	els.actionInput.value = text;
	await emitTelemetry(
		"extension_selection_pull",
		startedAt,
		"ok",
		text.slice(0, 24),
	);
	setStatus("Selection pulled into the side panel.");
});

els.saveActionButton.addEventListener("click", async () => {
	const value = String(els.actionInput.value || "").trim();
	if (!value) {
		setStatus("Capture or type a note before writing the durable action.");
		return;
	}
	const startedAt = performance.now();
	try {
		await authedFetchJson("/v1/workspace/action", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ kind: "capture", value, source: "extension" }),
		});
	} catch (error) {
		const outcome = await handleRuntimeFailure(
			"extension_action_write",
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
	await emitTelemetry(
		"extension_action_write",
		startedAt,
		"ok",
		value.slice(0, 24),
	);
	clearDegradedState();
	els.actionInput.value = "";
	await refreshRuntime();
	setStatus("Durable action written from the extension panel.");
});

// ---------- digest flow ----------
// Keep background job triggering separate so the request path and job path remain visible.
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
				"Idempotency-Key": `ext-${Date.now()}`,
			},
			body: JSON.stringify({ workspaceId, waitForFinish: true }),
		});
	} catch (error) {
		const outcome = await handleRuntimeFailure(
			"extension_digest_run",
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
	await emitTelemetry("extension_digest_run", startedAt, "ok", workspaceId);
	clearDegradedState();
	await refreshRuntime();
	setStatus("Digest job completed from the extension path.");
});

// ---------- runtime refresh ----------
// Reuse one refresh path so auth continuity and workspace reads stay aligned.
async function refreshRuntime() {
	const token = await readToken();
	if (!token) {
		clearDegradedState();
		showSignedOut();
		setStatus("No active extension session yet.");
		return;
	}

	const startedAt = performance.now();
	try {
		const identity = await authedFetchJson("/v1/identity", { method: "GET" });
		const workspace = await authedFetchJson("/v1/workspace/bootstrap", {
			method: "GET",
		});
		await emitTelemetry(
			"extension_workspace_bootstrap",
			startedAt,
			"ok",
			identity.payload.email,
		);
		clearDegradedState();
		showSignedIn(identity.payload, workspace.payload);
		setStatus(`Extension workspace ready for ${identity.payload.email}.`);
	} catch (error) {
		await handleRuntimeFailure(
			"extension_workspace_bootstrap",
			startedAt,
			error,
			"the workspace refresh",
			refreshRuntime,
		);
		return;
	}
}

// ---------- storage ----------
// Keep token access behind one helper so future auth changes touch one seam.
async function readToken() {
	const data = await chrome.storage.local.get(TOKEN_KEY);
	return data[TOKEN_KEY] || "";
}

// ---------- view rendering ----------
// Keep the signed-in and signed-out render paths small so panel state stays obvious.
function showSignedIn(identity, workspacePayload) {
	els.authSection.classList.add("hidden");
	els.workspaceSection.classList.remove("hidden");
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
	els.authSection.classList.remove("hidden");
	els.workspaceSection.classList.add("hidden");
	els.identityEmail.textContent = "—";
	els.bridgeCode.textContent = "—";
	els.workspaceId.textContent = "—";
	els.lastDigest.textContent = "—";
	els.latestEval.textContent = "—";
	els.recentActions.innerHTML = "";
}

function showSessionHeld() {
	els.authSection.classList.add("hidden");
	els.workspaceSection.classList.remove("hidden");
}

function renderActions(actions) {
	els.recentActions.innerHTML = "";
	for (const action of actions) {
		const item = document.createElement("li");
		item.textContent = `${action.kind} • ${action.source} • ${action.value}`;
		els.recentActions.appendChild(item);
	}
}

// ---------- fetch helpers ----------
// Keep public and authed fetch paths aligned with the web shell contract.
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
	const token = await readToken();
	return fetchJson(path, {
		...init,
		headers: {
			...(init.headers || {}),
			Authorization: `Bearer ${token}`,
		},
	});
}

// ---------- telemetry ----------
// Emit lightweight proof telemetry without blocking the panel interaction path.
async function emitTelemetry(name, startedAt, status, detail) {
	const durationMs = Number((performance.now() - startedAt).toFixed(2));
	await fetch(`${API_BASE_URL}/v1/telemetry/emit`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({
			surface: "extension",
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
		await chrome.storage.local.remove(TOKEN_KEY);
		clearDegradedState();
		showSignedOut();
		setStatus(
			"Stored extension session expired or was invalid, so the panel returned to signed-out state.",
		);
		return { handled: true, kind: "auth" };
	}
	showSessionHeld();
	setDegradedState(TRANSIENT_ERROR_MESSAGE, retryLabel, retryAction);
	setStatus(TRANSIENT_ERROR_MESSAGE);
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

// ---------- status ----------
// Keep operator-visible status text in one place for easier debugging.
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

async function recordPanelRuntimeEvidence() {
	const requested = await chrome.storage.local
		.get(PANEL_OPEN_REQUEST_KEY)
		.catch(() => ({}));
	const requestedAt = Number(requested[PANEL_OPEN_REQUEST_KEY] || 0);
	await chrome.storage.local
		.set({
			[PANEL_RUNTIME_EVIDENCE_KEY]: {
				bootedAt: Date.now(),
				documentReadyState: document.readyState,
				href: window.location.href,
				panelSurfaceReadyMs: Number(performance.now().toFixed(2)),
				requestAgeMs: requestedAt ? Date.now() - requestedAt : null,
			},
		})
		.catch(() => null);
}
