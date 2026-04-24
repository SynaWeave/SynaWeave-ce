/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  provide the bounded page-context bridge that returns plain selected text to the Sprint 1 side-panel runtime

- Later Extension Points:
  --> widen the bridge only when richer capture context becomes a durable extension concern

- Role:
  --> listens for the versioned selection request used by the side-panel shell
  --> keeps page-context access out of popup code so the MV3 boundary remains explicit

- Exports:
  --> foreground runtime side effects only

- Consumed By:
  --> `apps/extension/popup_script.ts` through runtime messaging on matched pages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

(() => {
	chrome.runtime.onMessage.addListener(
		(
			message: { type?: string } | undefined,
			_sender: ChromeRuntimeMessageSender,
			sendResponse: (response: { ok: boolean; text: string }) => void,
		) => {
			if (message?.type !== "selection:get") {
				return false;
			}

			try {
				const selection = window.getSelection();
				sendResponse({
					ok: true,
					text: selection ? String(selection).trim() : "",
				});
			} catch {
				sendResponse({ ok: false, text: "" });
			}

			return false;
		},
	);
})();
