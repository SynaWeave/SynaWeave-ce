/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  keep the extension options route as a bounded operator harness for the real side-panel runtime

- Later Extension Points:
  --> replace this harness with governed options behavior only when the extension settings path becomes active

- Role:
  --> gives operators and Playwright one user-gesture path that asks Chromium to open the side panel
  --> preserves the options entrypoint until the governed settings flow lands

- Exports:
  --> script side effects only

- Consumed By:
  --> the extension options page through `apps/extension/options.html`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

interface PanelEvidence {
	bootedAt: number;
	documentReadyState: string;
	href: string;
	panelSurfaceReadyMs: number;
	requestAgeMs: number | null;
}

interface OptionsPanelEvidence extends PanelEvidence {
	openToBootMs: number;
	requestedAt: number;
}

type OptionsWindow = Window & {
	__synaweaveOptionsPanelEvidence?: OptionsPanelEvidence | null;
};

(() => {
	// ---------- dom and storage keys ----------
	const PANEL_OPEN_REQUEST_KEY = "synaweave.sidePanelOpenRequestedAt";
	const PANEL_RUNTIME_EVIDENCE_KEY = "synaweave.sidePanelRuntimeEvidence";

	const els = {
		openSidePanelButton: getOptionalElement<HTMLButtonElement>(
			"open-side-panel-button",
		),
		statusLine: getOptionalElement<HTMLElement>("options-status-line"),
	};

	els.openSidePanelButton?.addEventListener("click", () => {
		void openSidePanelFromHarness();
	});

	// ---------- harness flow ----------
	async function openSidePanelFromHarness(): Promise<void> {
		const requestedAt = Date.now();
		setStatus(
			"Opening the browser-owned side panel from the extension harness...",
		);
		await chrome.storage.local.remove([PANEL_RUNTIME_EVIDENCE_KEY]);
		await chrome.storage.local.set({ [PANEL_OPEN_REQUEST_KEY]: requestedAt });

		const [tab] = await chrome.tabs.query({
			active: true,
			currentWindow: true,
		});
		if (!tab || typeof tab.id !== "number") {
			setStatus("No active tab was available for the side-panel request.");
			return;
		}

		try {
			await chrome.sidePanel.setOptions({
				tabId: tab.id,
				enabled: true,
				path: "popup.html",
			});
			await chrome.sidePanel.open({ windowId: tab.windowId });
		} catch (error) {
			setStatus(`Side panel open failed: ${String(error)}`);
			return;
		}

		const evidence = await waitForPanelEvidence(requestedAt);
		if (!evidence) {
			getOptionsWindow().__synaweaveOptionsPanelEvidence = null;
			setStatus(
				"Side panel open request reached Chromium, but this harness did not observe a matching panel document boot.",
			);
			return;
		}

		const openToBootMs = evidence.bootedAt - requestedAt;
		getOptionsWindow().__synaweaveOptionsPanelEvidence = {
			...evidence,
			openToBootMs,
			requestedAt,
		};
		setStatus(
			`Side panel opened and reported popup runtime boot in ${openToBootMs} ms.`,
		);
	}

	async function waitForPanelEvidence(
		requestedAt: number,
	): Promise<PanelEvidence | null> {
		const deadline = Date.now() + 5_000;
		while (Date.now() < deadline) {
			const data = await chrome.storage.local.get([PANEL_RUNTIME_EVIDENCE_KEY]);
			const evidence = data[PANEL_RUNTIME_EVIDENCE_KEY];
			if (isPanelEvidence(evidence) && evidence.bootedAt >= requestedAt) {
				return evidence;
			}
			await new Promise<void>((resolve) => {
				window.setTimeout(resolve, 100);
			});
		}
		return null;
	}

	// ---------- status ----------
	function setStatus(message: string): void {
		if (els.statusLine) {
			els.statusLine.textContent = message;
		}
	}

	function getOptionalElement<T extends HTMLElement>(id: string): T | null {
		const element = document.getElementById(id);
		if (!(element instanceof HTMLElement)) {
			return null;
		}
		return element as T;
	}

	function isPanelEvidence(value: unknown): value is PanelEvidence {
		if (!value || typeof value !== "object") {
			return false;
		}

		const candidate = value as Partial<PanelEvidence>;
		return (
			typeof candidate.bootedAt === "number" &&
			typeof candidate.documentReadyState === "string" &&
			typeof candidate.href === "string" &&
			typeof candidate.panelSurfaceReadyMs === "number" &&
			(candidate.requestAgeMs === null ||
				typeof candidate.requestAgeMs === "number")
		);
	}

	function getOptionsWindow(): OptionsWindow {
		return window as OptionsWindow;
	}
})();
