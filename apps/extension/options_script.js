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

// ---------- dom and storage keys ----------
const PANEL_OPEN_REQUEST_KEY = "synawave.sidePanelOpenRequestedAt";
const PANEL_RUNTIME_EVIDENCE_KEY = "synawave.sidePanelRuntimeEvidence";

const els = {
	openSidePanelButton: document.getElementById("open-side-panel-button"),
	statusLine: document.getElementById("options-status-line"),
};

els.openSidePanelButton?.addEventListener("click", () => {
	void openSidePanelFromHarness();
});

// ---------- harness flow ----------
async function openSidePanelFromHarness() {
	const requestedAt = Date.now();
	setStatus(
		"Opening the browser-owned side panel from the extension harness...",
	);
	await chrome.storage.local.remove(PANEL_RUNTIME_EVIDENCE_KEY);
	await chrome.storage.local.set({ [PANEL_OPEN_REQUEST_KEY]: requestedAt });

	const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
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
		window.__synawaveOptionsPanelEvidence = null;
		setStatus(
			"Side panel open request reached Chromium, but this harness did not observe a matching panel document boot.",
		);
		return;
	}

	const openToBootMs = evidence.bootedAt - requestedAt;
	window.__synawaveOptionsPanelEvidence = {
		...evidence,
		openToBootMs,
		requestedAt,
	};
	setStatus(
		`Side panel opened and reported popup runtime boot in ${openToBootMs} ms.`,
	);
}

async function waitForPanelEvidence(requestedAt) {
	const deadline = Date.now() + 5_000;
	while (Date.now() < deadline) {
		const data = await chrome.storage.local.get(PANEL_RUNTIME_EVIDENCE_KEY);
		const evidence = data[PANEL_RUNTIME_EVIDENCE_KEY];
		if (evidence && Number(evidence.bootedAt || 0) >= requestedAt) {
			return evidence;
		}
		await new Promise((resolve) => window.setTimeout(resolve, 100));
	}
	return null;
}

// ---------- status ----------
function setStatus(message) {
	if (els.statusLine) {
		els.statusLine.textContent = message;
	}
}
