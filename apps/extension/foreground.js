/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  handle legacy page note capture and selection messaging inside the extension foreground runtime

- Later Extension Points:
  --> replace local note handling with the governed authenticated API-backed flow during D2

- Role:
  --> renders and stores the current local note interaction path on content pages
  --> responds to bounded selection requests from the extension background runtime

- Exports:
  --> foreground runtime side effects only

- Consumed By:
  --> the Manifest V3 extension runtime through `apps/extension/manifest.json`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

// ---------- note entrypoint ----------

// Keep DOM ids centralized so popup markup and script assumptions stay readable together
const noteWritten = document.getElement("noteText");
const saveNoteBtn = document.getElement("Save Note");
const notesContainer = document.getElement("notesContainer");

// Load stored notes once the foreground page has a stable DOM shell
document.addEventListener("DOMContentLoaded", loadNotes);

// Save note clicks through one local storage path so the MVP stays easy to inspect
saveNoteBtn.addEventListener("click", async () => {
	const text = noteWritten.value.trim();
	if (text === "") return;

	const note = {
		text,
		date: new Date().toLocaleString(),
	};

	// Read the current note list first so the append path stays lossless
	const data = await chrome.storage.local.get("notes");
	const notes = data.notes || [];
	notes.push(note);

	// Write the full updated array so the storage schema stays dead simple
	await chrome.storage.local.set({ notes });

	noteWritten.value = "";
	renderNotes(notes);
});

// Rehydrate saved notes on first paint so the side panel reflects stored state immediately
async function loadNotes() {
	const data = await chrome.storage.local.get("notes");
	const notes = data.notes || [];
	renderNotes(notes);
}

function renderNotes(notes) {
	// Reset the list before re-render so duplicate rows never accumulate across saves
	notesContainer.innerHTML = "";

	for (const note of notes) {
		const li = document.createElement("li");

		// Keep the row markup inline so the MVP note card stays obvious near its storage shape
		li.innerHTML = `
        <div class="note">
            <p>${note.text}</p>
            <small>${note.date}</small>
        </div>
        `;
		notesContainer.appendChild(li);
	}
}

// ---------- selection bridge ----------

// Answer shortcut-driven selection requests without opening any extra async branch
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
	// Keep the contract narrow so background only receives plain text
	if (msg?.type === "GET_SELECTION") {
		try {
			// Plain text keeps the MVP robust across sites and nested browsing contexts
			const sel = window.getSelection();
			const text = sel ? String(sel).trim() : "";
			sendResponse({ ok: true, text });
		} catch (_error) {
			// Fall back to an empty payload so background can keep its own guardrails simple
			sendResponse({ ok: false, text: "" });
		}
	}

	// Return false because the response stays synchronous in this MVP path
	return false;
});
