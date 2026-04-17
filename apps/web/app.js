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

const els = {
	authCard: document.getElementById("auth-card"),
	workspaceCard: document.getElementById("workspace-card"),
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

void refreshRuntime();

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
	await emitTelemetry("web_sign_in", startedAt, "ok", `email:${email}`);
	await refreshRuntime();
});

els.signOutButton.addEventListener("click", async () => {
	localStorage.removeItem(TOKEN_KEY);
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
	await authedFetchJson("/v1/workspace/action", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ kind: "note", value, source: "web" }),
	});
	await emitTelemetry("web_action_write", startedAt, "ok", value.slice(0, 24));
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
	await authedFetchJson("/v1/jobs/workspace", {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			"Idempotency-Key": `web-${Date.now()}`,
		},
		body: JSON.stringify({ workspaceId, waitForFinish: true }),
	});
	await emitTelemetry("web_digest_run", startedAt, "ok", workspaceId);
	await refreshRuntime();
	setStatus("Background digest completed and reloaded.");
});

async function refreshRuntime() {
	const token = localStorage.getItem(TOKEN_KEY);
	if (!token) {
		showSignedOut();
		setStatus("No active web session yet.");
		return;
	}

	try {
		const startedAt = performance.now();
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
		showSignedIn(identity.payload, workspace.payload);
		setStatus(`Workspace ready for ${identity.payload.email}.`);
	} catch (_error) {
		localStorage.removeItem(TOKEN_KEY);
		showSignedOut();
		setStatus(
			"Stored session was invalid, so the web shell returned to signed-out state.",
		);
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

function renderActions(actions) {
	els.recentActions.innerHTML = "";
	for (const action of actions) {
		const item = document.createElement("li");
		item.textContent = `${action.kind} • ${action.source} • ${action.value}`;
		els.recentActions.appendChild(item);
	}
}

async function fetchJson(path, init) {
	const response = await fetch(`${API_BASE_URL}${path}`, init);
	if (!response.ok) {
		throw new Error(`Request failed: ${response.status}`);
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

function setStatus(message) {
	els.statusLine.textContent = message;
}
