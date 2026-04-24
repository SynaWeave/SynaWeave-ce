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

interface AuthLinkPayload {
	token: string;
	identity: IdentityPayload;
	workspace: WorkspacePayload;
	bridgeCode: string;
}

interface IdentityPayload {
	email: string;
	bridgeCode: string;
}

interface WorkspaceAction {
	kind: string;
	source: string;
	value: string;
}

interface WorkspacePayload {
	workspace: {
		workspaceId: string;
		lastDigest: string | null;
	};
	latestEval: {
		label: string;
		score: number | string;
	} | null;
	recentActions: WorkspaceAction[];
}

interface ApiPayloadResponse<T> {
	payload: T;
}

interface JobPayload {
	summary: string;
	workspaceBootstrap: WorkspacePayload;
}

interface RuntimeFailure {
	kind: "auth" | "transient";
	retryable: boolean;
	status: number;
	message: string;
}

interface RuntimeOutcome {
	handled: true;
	kind: RuntimeFailure["kind"];
}

interface PanelEvidenceRecord {
	bootedAt: number;
	documentReadyState: string;
	href: string;
	panelSurfaceReadyMs: number;
	requestAgeMs: number | null;
}

type JsonHeaders = Record<string, string>;

type JsonRequestInit = Omit<RequestInit, "headers"> & {
	headers?: JsonHeaders;
};

(() => {
	// ---------- runtime config ----------
	// Keep local API targeting explicit so the side-panel proof works without a bundler.
	const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
	const API_BASE_URL_KEY = "synaweave.apiBaseUrl";
	const TOKEN_KEY = "synaweave.extensionToken";
	const PANEL_OPEN_REQUEST_KEY = "synaweave.sidePanelOpenRequestedAt";
	const PANEL_RUNTIME_EVIDENCE_KEY = "synaweave.sidePanelRuntimeEvidence";
	const TRANSIENT_ERROR_MESSAGE =
		"Temporary API or provider failure. Session kept so you can retry.";

	// ---------- dom handles ----------
	// Keep selectors centralized so state transitions stay easy to review.
	const els = {
		authSection: requireElement<HTMLElement>("auth-section"),
		workspaceSection: requireElement<HTMLElement>("workspace-section"),
		degradedCard: requireElement<HTMLElement>("ext-degraded-card"),
		degradedMessage: requireElement<HTMLElement>("ext-degraded-message"),
		retryButton: requireElement<HTMLButtonElement>("ext-retry-button"),
		emailInput: requireElement<HTMLInputElement>("ext-email-input"),
		signInButton: requireElement<HTMLButtonElement>("ext-sign-in-button"),
		signOutButton: requireElement<HTMLButtonElement>("ext-sign-out-button"),
		identityEmail: requireElement<HTMLElement>("ext-identity-email"),
		bridgeCode: requireElement<HTMLElement>("ext-bridge-code"),
		workspaceId: requireElement<HTMLElement>("ext-workspace-id"),
		actionInput: requireElement<HTMLTextAreaElement>("ext-action-input"),
		pullSelectionButton: requireElement<HTMLButtonElement>(
			"pull-selection-button",
		),
		saveActionButton: requireElement<HTMLButtonElement>(
			"save-extension-action-button",
		),
		runJobButton: requireElement<HTMLButtonElement>("run-extension-job-button"),
		lastDigest: requireElement<HTMLElement>("ext-last-digest"),
		latestEval: requireElement<HTMLElement>("ext-latest-eval"),
		recentActions: requireElement<HTMLUListElement>("ext-recent-actions"),
		statusLine: requireElement<HTMLElement>("panel-status-line"),
	};

	const runtimeState: {
		retryAction: (() => Promise<void>) | null;
		retryLabel: string;
	} = {
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
		const response = await fetchJson<ApiPayloadResponse<AuthLinkPayload>>(
			"/v1/auth/link",
			{
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ email, surface: "extension" }),
			},
		);
		await chrome.storage.local.set({ [TOKEN_KEY]: response.payload.token });
		localStorage.setItem(TOKEN_KEY, response.payload.token);
		clearDegradedState();
		showSignedIn(response.payload.identity, response.payload.workspace);
		setStatus(
			`Extension workspace ready for ${response.payload.identity.email}.`,
		);
		await emitTelemetry("extension_sign_in", startedAt, "ok", email);
	});

	els.signOutButton.addEventListener("click", async () => {
		await chrome.storage.local.remove(TOKEN_KEY);
		localStorage.removeItem(TOKEN_KEY);
		clearDegradedState();
		showSignedOut();
		setStatus("Signed out of the extension panel.");
	});

	// ---------- selection and write flow ----------
	// Keep capture and durable write actions explicit so the panel proves each runtime step.
	els.pullSelectionButton.addEventListener("click", async () => {
		const startedAt = performance.now();
		const [tab] = await chrome.tabs.query({
			active: true,
			currentWindow: true,
		});
		if (!tab || typeof tab.id !== "number") {
			setStatus("No active tab was available for selection capture.");
			return;
		}
		const response = await chrome.tabs
			.sendMessage(tab.id, { type: "selection:get" })
			.catch(() => null);
		const text = String(
			(response as { text?: unknown } | null)?.text || "",
		).trim();
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
		await submitAction();
	});

	els.runJobButton.addEventListener("click", async () => {
		await runDigestJob();
	});

	async function submitAction(): Promise<void> {
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
				submitAction,
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
		prependAction({ kind: "capture", source: "extension", value });
		els.actionInput.value = "";
		setStatus("Durable action written from the extension panel.");
	}

	// ---------- digest flow ----------
	// Keep background job triggering separate so the request path and job path remain visible.
	async function runDigestJob(): Promise<void> {
		const workspaceId = els.workspaceId.textContent || "";
		if (!workspaceId || workspaceId === "—") {
			setStatus("No workspace is ready yet.");
			return;
		}
		const startedAt = performance.now();
		const identity = currentIdentity();
		try {
			const response = await authedFetchJson<ApiPayloadResponse<JobPayload>>(
				"/v1/jobs/workspace",
				{
					method: "POST",
					headers: {
						"Content-Type": "application/json",
						"Idempotency-Key": `ext-${Date.now()}`,
					},
					body: JSON.stringify({ workspaceId, waitForFinish: true }),
				},
			);
			showSignedIn(identity, response.payload.workspaceBootstrap);
		} catch (error) {
			const outcome = await handleRuntimeFailure(
				"extension_digest_run",
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
		await emitTelemetry("extension_digest_run", startedAt, "ok", workspaceId);
		clearDegradedState();
		setStatus("Digest job completed from the extension path.");
	}

	// ---------- runtime refresh ----------
	// Reuse one refresh path so auth continuity and workspace reads stay aligned.
	async function refreshRuntime(): Promise<void> {
		const token = await readToken();
		if (!token) {
			clearDegradedState();
			showSignedOut();
			setStatus("No active extension session yet.");
			return;
		}

		const startedAt = performance.now();
		try {
			const identity = await authedFetchJson<
				ApiPayloadResponse<IdentityPayload>
			>("/v1/identity", { method: "GET" });
			const workspace = await authedFetchJson<
				ApiPayloadResponse<WorkspacePayload>
			>("/v1/workspace/bootstrap", { method: "GET" });
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
		}
	}

	// ---------- storage ----------
	// Keep token access behind one helper so future auth changes touch one seam.
	async function readToken(): Promise<string> {
		const localToken = localStorage.getItem(TOKEN_KEY);
		if (localToken) {
			return localToken;
		}
		const data = await chrome.storage.local.get([TOKEN_KEY]);
		if (typeof data[TOKEN_KEY] === "string") {
			localStorage.setItem(TOKEN_KEY, data[TOKEN_KEY]);
			return data[TOKEN_KEY];
		}
		return "";
	}

	async function readApiBaseUrl(): Promise<string> {
		const data: Record<string, unknown> = await chrome.storage.local
			.get([API_BASE_URL_KEY])
			.catch(() => ({}));
		return typeof data[API_BASE_URL_KEY] === "string"
			? data[API_BASE_URL_KEY]
			: DEFAULT_API_BASE_URL;
	}

	// ---------- view rendering ----------
	// Keep the signed-in and signed-out render paths small so panel state stays obvious.
	function showSignedIn(
		identity: IdentityPayload,
		workspacePayload: WorkspacePayload,
	): void {
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

	function showSignedOut(): void {
		els.authSection.classList.remove("hidden");
		els.workspaceSection.classList.add("hidden");
		els.identityEmail.textContent = "—";
		els.bridgeCode.textContent = "—";
		els.workspaceId.textContent = "—";
		els.lastDigest.textContent = "—";
		els.latestEval.textContent = "—";
		els.recentActions.innerHTML = "";
	}

	function showSessionHeld(): void {
		els.authSection.classList.add("hidden");
		els.workspaceSection.classList.remove("hidden");
	}

	function renderActions(actions: WorkspaceAction[]): void {
		els.recentActions.innerHTML = "";
		for (const action of actions) {
			const item = document.createElement("li");
			item.textContent = `${action.kind} • ${action.source} • ${action.value}`;
			els.recentActions.appendChild(item);
		}
	}

	function prependAction(action: WorkspaceAction): void {
		renderActions([action, ...currentActions()].slice(0, 5));
	}

	function currentActions(): WorkspaceAction[] {
		return Array.from(els.recentActions.querySelectorAll("li")).flatMap(
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
			email: els.identityEmail.textContent || "",
			bridgeCode: els.bridgeCode.textContent || "",
		};
	}

	// ---------- fetch helpers ----------
	// Keep public and authed fetch paths aligned with the web shell contract.
	async function fetchJson<T>(path: string, init: JsonRequestInit): Promise<T> {
		const apiBaseUrl = await readApiBaseUrl();
		let response: Response;
		try {
			response = await fetch(`${apiBaseUrl}${path}`, {
				...init,
				headers: {
					...(init.headers || {}),
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

	async function authedFetchJson<T>(
		path: string,
		init: JsonRequestInit,
	): Promise<T> {
		const token = await readToken();
		return fetchJson<T>(path, {
			...init,
			headers: {
				...(init.headers || {}),
				Authorization: `Bearer ${token}`,
			},
		});
	}

	// ---------- telemetry ----------
	// Emit lightweight proof telemetry without blocking the panel interaction path.
	async function emitTelemetry(
		name: string,
		startedAt: number,
		status: string,
		detail: string,
	): Promise<void> {
		const durationMs = Number((performance.now() - startedAt).toFixed(2));
		const apiBaseUrl = await readApiBaseUrl();
		const token = await readToken();
		await fetch(`${apiBaseUrl}/v1/telemetry/emit`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				...(token ? { Authorization: `Bearer ${token}` } : {}),
			},
			body: JSON.stringify({
				surface: "extension",
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
	): Promise<RuntimeOutcome> {
		const failure = normalizeRuntimeError(error);
		await emitTelemetry(
			telemetryName,
			startedAt,
			failure.kind === "auth" ? "error" : "degraded",
			buildFailureTelemetryDetail(failure),
		);
		if (failure.kind === "auth") {
			await chrome.storage.local.remove(TOKEN_KEY);
			localStorage.removeItem(TOKEN_KEY);
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

	function setDegradedState(
		message: string,
		retryLabel: string,
		retryAction: () => Promise<void>,
	): void {
		runtimeState.retryAction = retryAction;
		runtimeState.retryLabel = retryLabel;
		els.degradedMessage.textContent = message;
		els.retryButton.textContent = `Retry ${retryLabel}`;
		els.degradedCard.classList.remove("hidden");
	}

	function clearDegradedState(): void {
		runtimeState.retryAction = null;
		runtimeState.retryLabel = "";
		els.degradedCard.classList.add("hidden");
		els.degradedMessage.textContent =
			"A retryable runtime issue is holding the current session.";
		els.retryButton.textContent = "Retry last request";
	}

	function normalizeRuntimeError(error: unknown): RuntimeFailure {
		if (isRuntimeFailure(error)) {
			return error;
		}
		return makeRuntimeError({
			kind: "transient",
			retryable: true,
			status: 0,
			message: error instanceof Error ? error.message : String(error),
		});
	}

	function makeRuntimeError(failure: RuntimeFailure): RuntimeFailure {
		return failure;
	}

	function buildFailureTelemetryDetail(failure: RuntimeFailure): string {
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

	// ---------- status ----------
	// Keep operator-visible status text in one place for easier debugging.
	function setStatus(message: string): void {
		els.statusLine.textContent = message;
	}

	function makeTraceHeaders(): JsonHeaders {
		const traceId = Array.from(crypto.getRandomValues(new Uint8Array(16)))
			.map((value) => value.toString(16).padStart(2, "0"))
			.join("");
		const spanId = Array.from(crypto.getRandomValues(new Uint8Array(8)))
			.map((value) => value.toString(16).padStart(2, "0"))
			.join("");
		return { traceparent: `00-${traceId}-${spanId}-01` };
	}

	async function recordPanelRuntimeEvidence(): Promise<void> {
		const requested: Record<string, unknown> = await chrome.storage.local
			.get([PANEL_OPEN_REQUEST_KEY])
			.catch(() => ({}));
		const requestedAt =
			typeof requested[PANEL_OPEN_REQUEST_KEY] === "number"
				? requested[PANEL_OPEN_REQUEST_KEY]
				: Number(requested[PANEL_OPEN_REQUEST_KEY] || 0);
		await chrome.storage.local
			.set({
				[PANEL_RUNTIME_EVIDENCE_KEY]: {
					bootedAt: Date.now(),
					documentReadyState: document.readyState,
					href: window.location.href,
					panelSurfaceReadyMs: Number(performance.now().toFixed(2)),
					requestAgeMs: requestedAt ? Date.now() - requestedAt : null,
				} satisfies PanelEvidenceRecord,
			})
			.catch(() => null);
	}

	function requireElement<T extends HTMLElement>(id: string): T {
		const element = document.getElementById(id);
		if (!(element instanceof HTMLElement)) {
			throw new Error(`Missing required extension element: ${id}`);
		}
		return element as T;
	}

	function isRuntimeFailure(value: unknown): value is RuntimeFailure {
		if (!value || typeof value !== "object") {
			return false;
		}

		const candidate = value as Partial<RuntimeFailure>;
		return (
			(candidate.kind === "auth" || candidate.kind === "transient") &&
			typeof candidate.retryable === "boolean" &&
			typeof candidate.status === "number" &&
			typeof candidate.message === "string"
		);
	}
})();
