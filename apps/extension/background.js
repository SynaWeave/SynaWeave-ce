/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  coordinate the Manifest V3 side-panel runtime and bounded extension message flows for the Sprint 1 proof path

- Later Extension Points:
  --> widen background coordination only when later queueing retry or richer extension events become durable concerns

- Role:
  --> keeps side-panel behavior stable across install startup and action clicks
  --> handles bounded runtime messages for selection shortcuts panel closing and operator-friendly diagnostics

- Exports:
  --> background worker side effects only

- Consumed By:
  --> the Manifest V3 runtime through `apps/extension/manifest.json`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

// ---------- side-panel bootstrap ----------
// Keep the default action tied to the panel so the main extension path stays discoverable.
function enableSidePanel() {
	return chrome.sidePanel
		.setPanelBehavior({ openPanelOnActionClick: true })
		.catch(() => null);
}

// ---------- install and startup ----------
// Re-apply startup behavior so extension upgrades do not depend on stale browser state.
chrome.runtime.onInstalled.addListener(() => {
	void enableSidePanel();
	chrome.contextMenus.create({
		id: "capture-selection",
		title: "Open SynaWave side panel",
		contexts: ["selection"],
	});
});

chrome.runtime.onStartup.addListener(() => {
	void enableSidePanel();
});

// ---------- action and capture entrypoints ----------
// Keep user-triggered panel open paths explicit across toolbar and context-menu flows.
chrome.action.onClicked.addListener((tab) => {
	if (!tab || typeof tab.id !== "number") {
		return;
	}

	void chrome.sidePanel
		.setOptions({ tabId: tab.id, enabled: true, path: "popup.html" })
		.then(() => chrome.sidePanel.open({ windowId: tab.windowId }))
		.catch(() => null);
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
	if (
		info.menuItemId !== "capture-selection" ||
		!tab ||
		typeof tab.id !== "number"
	) {
		return;
	}
	void chrome.sidePanel.open({ windowId: tab.windowId }).catch(() => null);
});

// ---------- keyboard shortcuts ----------
// Keep the first runtime shortcut set small so the background worker stays easy to audit.
chrome.commands.onCommand.addListener(async (command) => {
	const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
	if (!tab || typeof tab.id !== "number") {
		return;
	}

	if (command === "open-study-panel") {
		await chrome.sidePanel.open({ windowId: tab.windowId }).catch(() => null);
	}

	if (command === "clip_selection") {
		await chrome.tabs
			.sendMessage(tab.id, { type: "selection:get" })
			.catch(() => null);
		await chrome.sidePanel.open({ windowId: tab.windowId }).catch(() => null);
	}
});

// ---------- runtime messages ----------
// Keep message handling versionable so the side-panel shell and background worker stay loosely coupled.
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
	if (message?.type === "panel:close") {
		if (sender.tab && typeof sender.tab.id === "number") {
			void chrome.sidePanel
				.setOptions({ tabId: sender.tab.id, enabled: false })
				.catch(() => null);
		}
		sendResponse({ ok: true });
		return false;
	}

	if (message?.type === "runtime:ping") {
		sendResponse({ ok: true, runtime: "extension-background" });
		return false;
	}

	return false;
});

// ---------- boot visibility ----------
// Enable the panel on worker load so startup and install share the same default behavior.
void enableSidePanel();
