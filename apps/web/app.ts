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

const API_BASE_URL_KEY = "synaweave.apiBaseUrl";
const TOKEN_KEY = "synaweave.webToken";
const API_BASE_URL =
	localStorage.getItem(API_BASE_URL_KEY) || "http://127.0.0.1:8000";
const TRANSIENT_ERROR_MESSAGE =
	"Temporary API or provider failure. Session kept so you can retry.";

type AuthLinkPayload = {
	token: string;
	identity: IdentityPayload;
	workspace: WorkspaceBootstrapPayload;
	bridgeCode: string;
};
type AuthLinkResponse = { payload: AuthLinkPayload };
type IdentityPayload = { email: string; bridgeCode: string };
type IdentityResponse = { payload: IdentityPayload };
type WorkspaceSummary = { workspaceId: string; lastDigest: string | null };
type WorkspaceEval = { label: string; score: string | number };
type WorkspaceAction = { kind: string; source: string; value: string };
type WorkspaceBootstrapPayload = {
	workspace: WorkspaceSummary;
	latestEval: WorkspaceEval | null;
	recentActions: WorkspaceAction[];
};
type WorkspaceBootstrapResponse = { payload: WorkspaceBootstrapPayload };
type JobPayload = {
	summary: string;
	workspaceBootstrap: WorkspaceBootstrapPayload;
};
type JobResponse = { payload: JobPayload };
type RuntimeErrorKind = "auth" | "transient";
type RuntimeError = {
	kind: RuntimeErrorKind;
	retryable: boolean;
	status: number;
	message: string;
};
type RuntimeFailureOutcome = { handled: true; kind: RuntimeErrorKind };
type RuntimeState = {
	retryAction: null | (() => Promise<void>);
	retryLabel: string;
	sessionToken: string | null;
};

const elems = {
	authCard: requireHtmlElement("auth-card"),
	workspaceCard: requireHtmlElement("workspace-card"),
	degradedCard: requireHtmlElement("degraded-card"),
	degradedMessage: requireHtmlElement("degraded-message"),
	retryButton: requireButtonElement("retry-button"),
	emailInput: requireInputElement("email-input"),
	signInButton: requireButtonElement("sign-in-button"),
	signOutButton: requireButtonElement("sign-out-button"),
	identityEmail: requireHtmlElement("identity-email"),
	bridgeCode: requireHtmlElement("bridge-code"),
	workspaceId: requireHtmlElement("workspace-id"),
	actionInput: requireTextAreaElement("action-input"),
	saveActionButton: requireButtonElement("save-action-button"),
	runJobButton: requireButtonElement("run-job-button"),
	lastDigest: requireHtmlElement("last-digest"),
	latestEval: requireHtmlElement("latest-eval"),
	recentActions: requireHtmlElement("recent-actions"),
	statusLine: requireHtmlElement("status-line"),
};

const runtimeState: RuntimeState = {
	retryAction: null,
	retryLabel: "",
	sessionToken: null,
};

void refreshRuntime();

elems.retryButton.addEventListener("click", async () => {
	const retryAction = runtimeState.retryAction;
	if (!retryAction) {
		setStatus("No retryable web request is waiting right now.");
		return;
	}
	setStatus(`Retrying ${runtimeState.retryLabel}.`);
	await retryAction();
});

elems.signInButton.addEventListener("click", async () => {
	const email = String(elems.emailInput.value || "").trim();
	if (!email) {
		setStatus("Enter an email before signing in.");
		return;
	}

	const startedAt = performance.now();
	const response = await fetchJson<AuthLinkResponse>("/v1/auth/link", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ email, surface: "web" }),
	});
	runtimeState.sessionToken = response.payload.token;
	localStorage.setItem(TOKEN_KEY, response.payload.token);
	clearDegradedState();
	showSignedIn(response.payload.identity, response.payload.workspace);
	setStatus(`Workspace ready for ${response.payload.identity.email}.`);
	await emitTelemetry("web_sign_in", startedAt, "ok", `email:${email}`);
});

elems.signOutButton.addEventListener("click", async () => {
	runtimeState.sessionToken = null;
	localStorage.removeItem(TOKEN_KEY);
	clearDegradedState();
	showSignedOut();
	setStatus("Signed out of the web shell.");
});

elems.saveActionButton.addEventListener("click", async () => {
	await submitAction();
});

elems.runJobButton.addEventListener("click", async () => {
	await runDigestJob();
});

async function submitAction(): Promise<void> {
	const value = String(elems.actionInput.value || "").trim();
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
			submitAction,
		);
		if (outcome.handled) {
			return;
		}
		throw error;
	}
	await emitTelemetry("web_action_write", startedAt, "ok", value.slice(0, 24));
	clearDegradedState();
	prependAction({ kind: "note", source: "web", value });
	elems.actionInput.value = "";
	setStatus("Durable action written through the API.");
}

async function runDigestJob(): Promise<void> {
	const workspaceId = elems.workspaceId.textContent || "";
	if (!workspaceId || workspaceId === "—") {
		setStatus("No workspace is ready yet.");
		return;
	}
	const startedAt = performance.now();
	const identity = currentIdentity();
	try {
		const response = await authedFetchJson<JobResponse>("/v1/jobs/workspace", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"Idempotency-Key": `web-${Date.now()}`,
			},
			body: JSON.stringify({ workspaceId, waitForFinish: true }),
		});
		showSignedIn(identity, response.payload.workspaceBootstrap);
	} catch (error) {
		const outcome = await handleRuntimeFailure(
			"web_digest_run",
			startedAt,
			error,
			"the digest job",
			runDigestJob,
		);
		if (outcome.handled) {
			return;
		}
		throw error;
	}
	await emitTelemetry("web_digest_run", startedAt, "ok", workspaceId);
	clearDegradedState();
	setStatus("Background digest completed and reloaded.");
}

async function refreshRuntime(): Promise<void> {
	const token = readToken();
	if (!token) {
		clearDegradedState();
		showSignedOut();
		setStatus("No active web session yet.");
		return;
	}

	const startedAt = performance.now();
	try {
		const identity = await authedFetchJson<IdentityResponse>("/v1/identity", {
			method: "GET",
		});
		const workspace = await authedFetchJson<WorkspaceBootstrapResponse>(
			"/v1/workspace/bootstrap",
			{
				method: "GET",
			},
		);
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

function showSignedIn(
	identity: IdentityPayload,
	workspacePayload: WorkspaceBootstrapPayload,
): void {
	elems.authCard.classList.add("hidden");
	elems.workspaceCard.classList.remove("hidden");
	elems.identityEmail.textContent = identity.email;
	elems.bridgeCode.textContent = identity.bridgeCode;
	elems.workspaceId.textContent = workspacePayload.workspace.workspaceId;
	elems.lastDigest.textContent =
		workspacePayload.workspace.lastDigest || "No digest yet.";
	elems.latestEval.textContent = workspacePayload.latestEval
		? `${workspacePayload.latestEval.label}: ${workspacePayload.latestEval.score}`
		: "No eval yet.";
	renderActions(workspacePayload.recentActions || []);
}

function showSignedOut(): void {
	elems.authCard.classList.remove("hidden");
	elems.workspaceCard.classList.add("hidden");
	elems.identityEmail.textContent = "—";
	elems.bridgeCode.textContent = "—";
	elems.workspaceId.textContent = "—";
	elems.lastDigest.textContent = "—";
	elems.latestEval.textContent = "—";
	elems.recentActions.innerHTML = "";
}

function showSessionHeld(): void {
	elems.authCard.classList.add("hidden");
	elems.workspaceCard.classList.remove("hidden");
}

function renderActions(actions: WorkspaceAction[]): void {
	elems.recentActions.innerHTML = "";
	for (const action of actions) {
		const item = document.createElement("li");
		item.textContent = `${action.kind} • ${action.source} • ${action.value}`;
		elems.recentActions.appendChild(item);
	}
}

function prependAction(action: WorkspaceAction): void {
	renderActions([action, ...currentActions()].slice(0, 5));
}

function currentActions(): WorkspaceAction[] {
	return Array.from(elems.recentActions.querySelectorAll("li")).flatMap(
		(item) => {
			const [kind, source, ...valueParts] =
				item.textContent?.split(" • ") || [];
			if (!kind || !source || valueParts.length === 0) {
				return [];
			}
			return [{ kind, source, value: valueParts.join(" • ") }];
		},
	);
}

function currentIdentity(): IdentityPayload {
	return {
		email: elems.identityEmail.textContent || "",
		bridgeCode: elems.bridgeCode.textContent || "",
	};
}

async function fetchJson<T>(path: string, init: RequestInit): Promise<T> {
	let response: Response;
	try {
		response = await fetch(`${API_BASE_URL}${path}`, {
			...init,
			headers: {
				...headersToObject(init.headers),
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
	return (await response.json()) as T;
}

async function authedFetchJson<T>(path: string, init: RequestInit): Promise<T> {
	const token = readToken();
	return fetchJson<T>(path, {
		...init,
		headers: {
			...headersToObject(init.headers),
			Authorization: `Bearer ${token}`,
		},
	});
}

async function emitTelemetry(
	name: string,
	startedAt: number,
	status: string,
	detail: string,
): Promise<void> {
	const durationMs = Number((performance.now() - startedAt).toFixed(2));
	const token = readToken();
	await fetch(`${API_BASE_URL}/v1/telemetry/emit`, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			...(token ? { Authorization: `Bearer ${token}` } : {}),
		},
		body: JSON.stringify({
			surface: "web",
			name,
			status,
			durationMs,
			detail,
		}),
	}).catch(() => null);
}

async function handleRuntimeFailure(
	telemetryName: string,
	startedAt: number,
	error: unknown,
	retryLabel: string,
	retryAction: () => Promise<void>,
): Promise<RuntimeFailureOutcome> {
	const failure = normalizeRuntimeError(error);
	await emitTelemetry(
		telemetryName,
		startedAt,
		failure.kind === "auth" ? "error" : "degraded",
		buildFailureTelemetryDetail(failure),
	);
	if (failure.kind === "auth") {
		runtimeState.sessionToken = null;
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

function setDegradedState(
	message: string,
	retryLabel: string,
	retryAction: () => Promise<void>,
): void {
	runtimeState.retryAction = retryAction;
	runtimeState.retryLabel = retryLabel;
	elems.degradedMessage.textContent = message;
	elems.retryButton.textContent = `Retry ${retryLabel}`;
	elems.degradedCard.classList.remove("hidden");
}

function clearDegradedState(): void {
	runtimeState.retryAction = null;
	runtimeState.retryLabel = "";
	elems.degradedCard.classList.add("hidden");
	elems.degradedMessage.textContent =
		"A retryable runtime issue is holding the current session.";
	elems.retryButton.textContent = "Retry last request";
}

function normalizeRuntimeError(error: unknown): RuntimeError {
	if (isRuntimeError(error)) {
		return error;
	}
	return makeRuntimeError({
		kind: "transient",
		retryable: true,
		status: 0,
		message: error instanceof Error ? error.message : String(error),
	});
}

function makeRuntimeError(runtimeError: RuntimeError): RuntimeError {
	const { kind, retryable, status, message } = runtimeError;
	return { kind, retryable, status, message };
}

function buildFailureTelemetryDetail(failure: RuntimeError): string {
	return [
		`kind=${failure.kind}`,
		`retryable=${String(failure.retryable)}`,
		`status=${failure.status || "network"}`,
		`message=${failure.message}`,
	]
		.join(" ")
		.slice(0, 180);
}

async function readFailureDetail(response: Response): Promise<string> {
	const contentType = response.headers.get("content-type") || "";
	if (contentType.includes("application/json")) {
		const body = (await response.json().catch(() => null)) as {
			detail?: unknown;
		} | null;
		const detail = body?.detail;
		if (typeof detail === "string" && detail.trim()) {
			return detail.trim();
		}
	}
	const text = await response.text().catch(() => "");
	return text.trim() || `Request failed: ${response.status}`;
}

function isAuthFailureStatus(status: number): boolean {
	return status === 401 || status === 403;
}

function setStatus(message: string): void {
	elems.statusLine.textContent = message;
}

function readToken(): string | null {
	if (runtimeState.sessionToken) {
		return runtimeState.sessionToken;
	}

	const token = localStorage.getItem(TOKEN_KEY);
	if (token) {
		runtimeState.sessionToken = token;
	}

	return token;
}

function requireElement(id: string): Element {
	const elem = document.getElementById(id);
	if (!elem) {
		throw new Error(`Missing required element: #${id}`);
	}
	return elem;
}

function requireHtmlElement(id: string): HTMLElement {
	const elem = requireElement(id);
	if (!(elem instanceof HTMLElement)) {
		throw new Error(`Expected HTMLElement for #${id}`);
	}
	return elem;
}

function requireButtonElement(id: string): HTMLButtonElement {
	const elem = requireElement(id);
	if (!(elem instanceof HTMLButtonElement)) {
		throw new Error(`Expected HTMLButtonElement for #${id}`);
	}
	return elem;
}

function requireInputElement(id: string): HTMLInputElement {
	const elem = requireElement(id);
	if (!(elem instanceof HTMLInputElement)) {
		throw new Error(`Expected HTMLInputElement for #${id}`);
	}
	return elem;
}

function requireTextAreaElement(id: string): HTMLTextAreaElement {
	const elem = requireElement(id);
	if (!(elem instanceof HTMLTextAreaElement)) {
		throw new Error(`Expected HTMLTextAreaElement for #${id}`);
	}
	return elem;
}

function makeTraceHeaders(): Record<string, string> {
	const traceId = Array.from(crypto.getRandomValues(new Uint8Array(16)))
		.map((value) => value.toString(16).padStart(2, "0"))
		.join("");
	const spanId = Array.from(crypto.getRandomValues(new Uint8Array(8)))
		.map((value) => value.toString(16).padStart(2, "0"))
		.join("");
	return { traceparent: `00-${traceId}-${spanId}-01` };
}

function isRuntimeError(error: unknown): error is RuntimeError {
	if (!error || typeof error !== "object") {
		return false;
	}

	const runtimeError = error as Partial<RuntimeError>;
	return (
		(runtimeError.kind === "auth" || runtimeError.kind === "transient") &&
		typeof runtimeError.retryable === "boolean" &&
		typeof runtimeError.status === "number" &&
		typeof runtimeError.message === "string"
	);
}

function headersToObject(headers?: HeadersInit): Record<string, string> {
	if (!headers) {
		return {};
	}

	return Object.fromEntries(new Headers(headers).entries());
}
