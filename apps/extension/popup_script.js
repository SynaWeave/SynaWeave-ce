/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  drive the legacy extension popup interactions for local card actions and panel closing

- Later Extension Points:
  --> replace local popup behavior with the governed authenticated extension shell during D2

- Role:
  --> wires the current popup controls to local legacy behaviors and panel closing
  --> keeps the popup interaction path explicit while the extension runtime is still being rebuilt

- Exports:
  --> popup runtime side effects only

- Consumed By:
  --> the popup and side-panel UI through `apps/extension/popup.html`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

// ---------- popup handles ----------

// Keep DOM ids centralized so popup markup and script assumptions stay readable together
const els = {
	btnRefresh: document.getElementById("btn-refresh"),
	btnExportAnki: document.getElementById("btn-export_anki"),
	btnCopyQuizlet: document.getElementById("btn-copy_quizlet"),
	qaFront: document.getElementById("qa_front"),
	qaBack: document.getElementById("qa_back"),
	qaTags: document.getElementById("qa_tags"),
	qaCreateBtn: document.getElementById("qa_createBtn"),
	dueList: document.getElementById("due_list"),
	btnClosePanel: document.getElementById("btn-close_panel"),
};

// ---------- panel close flow ----------

// Reuse the cached button so close behavior never depends on a second DOM lookup
const closePanelButton = els.btnClosePanel;

if (closePanelButton) {
	closePanelButton.addEventListener("click", function handleCloseClick(event) {
		// Ask background to hide the panel before this popup context tears itself down
		chrome.runtime.sendMessage({ type: "panel:close_request" }, () => {
			// Read runtime.lastError so Chrome does not treat the callback as unhandled
			void chrome.runtime.lastError;

			// Close on the next tick so the background request gets one chance to land first
			setTimeout(() => {
				try {
					window.close();
				} catch (_error) {
					// Keep close failures quiet because popup and side-panel teardown differ by surface
				}
			}, 0);
		});

		// Block default button behavior so the close path stays single-route
		if (event && typeof event.preventDefault === "function") {
			event.preventDefault();
		}
	});
}

// ---------- reserved popup surface ----------

// Keep current popup handles referenced so the reserved MVP controls stay visible to reviewers
void els;
