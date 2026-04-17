/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  run the legacy extension background behaviors for panel control storage and local card actions

- Later Extension Points:
  --> replace local-only storage and export behavior with the governed API-backed runtime path during D2

- Role:
  --> manages side-panel opening behavior for the current extension shell
  --> owns the bounded local storage and export helper path used by the legacy extension runtime

- Exports:
  --> background worker side effects only

- Consumed By:
  --> the Manifest V3 extension runtime through `apps/extension/manifest.json`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

// ---------- panel bootstrap ----------

// Ask Chrome for built-in side-panel behavior as soon as the worker boots
chrome.sidePanel
	.setPanelBehavior({ openPanelOnActionClick: true })
	.catch((_error) => {
		// Keep startup failures quiet because older Chrome channels can miss this capability
	});

// Re-apply panel behavior on install so fresh extension state stays predictable
chrome.runtime.onInstalled.addListener(() => {
	chrome.sidePanel
		.setPanelBehavior({ openPanelOnActionClick: true })
		.catch((_error) => {
			// Keep install fallback silent because the explicit click handler still covers open behavior
		});
});

// Re-apply panel behavior on browser startup so upgrades do not depend on stale extension state
chrome.runtime.onStartup.addListener(() => {
	chrome.sidePanel
		.setPanelBehavior({ openPanelOnActionClick: true })
		.catch((_error) => {
			// Keep startup retries quiet because Chrome channel support still varies here
		});
});

// Keep an explicit click fallback so the panel still opens when built-in behavior drifts
chrome.action.onClicked.addListener((clickedTab) => {
	// Skip tabs without ids because sidePanel options need a concrete tab target
	if (!clickedTab || typeof clickedTab.id !== "number") {
		return;
	}

	// Re-enable the panel before opening so earlier close flows cannot strand the tab disabled
	chrome.sidePanel
		.setOptions({
			tabId: clickedTab.id,
			enabled: true,
			path: "popup.html",
		})
		.then(() => {
			// Open against the current window so the click and visible panel stay in sync
			return chrome.sidePanel.open({ windowId: clickedTab.windowId });
		})
		.catch((_error) => {
			// Keep fallback failures quiet because most are transient channel-specific panel limits
		});
});

// ---------- storage contract ----------

// Keep storage keys centralized so popup and background state labels do not drift
const STORE_KEYS = {
	CARDS: "cards",
	PREFS: "prefs",
};

async function loadCards() {
	// Default to an empty list so first-run review flows skip null guards
	const { [STORE_KEYS.CARDS]: cards = [] } = await chrome.storage.local.get(
		STORE_KEYS.CARDS,
	);
	return cards;
}

async function saveCards(cards) {
	// Write the whole card list so local MVP persistence stays traceable
	await chrome.storage.local.set({ [STORE_KEYS.CARDS]: cards });
}

async function loadPrefs() {
	// Merge defaults on read so partial future prefs never break call sites
	const { [STORE_KEYS.PREFS]: prefs = defaultPrefs() } =
		await chrome.storage.sync.get(STORE_KEYS.PREFS);
	return Object.assign(defaultPrefs(), prefs);
}

async function savePrefs(prefs) {
	// Keep sync storage isolated to preferences so review cards stay local-only
	await chrome.storage.sync.set({ [STORE_KEYS.PREFS]: prefs });
}

function defaultPrefs() {
	// Keep defaults inline so operator-visible behavior stays obvious without cross-file lookup
	return {
		destinations: {
			local: true,
			exportAnki: true,
			exportQuizlet: true,
			ankiConnect: false,
		},
		dailyReminderHour: 9,
	};
}

// Keep prefs helpers referenced until the settings flow starts using them directly
void loadPrefs;
void savePrefs;

// ---------- card shaping ----------

// Build compact local ids without introducing a heavier persistence dependency
function makeId() {
	return `c_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

// Normalize raw inputs once so every save path produces the same card shape
function createCard({
	front,
	back = "",
	tags = [],
	srcTitle = "",
	srcUrl = "",
}) {
	const now = Date.now();
	return {
		id: makeId(),
		front: (front || "").trim(),
		back: (back || "").trim(),
		tags,
		srcTitle,
		srcUrl,
		ease: 2.5,
		interval: 0,
		reps: 0,
		dueAt: now,
		createdAt: now,
		updatedAt: now,
	};
}

// ---------- shortcut flow ----------

// Ask the foreground page for selected text before creating a local review card
chrome.commands.onCommand.addListener(async (command) => {
	const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
	if (!tab || typeof tab.id !== "number") {
		return;
	}

	if (command === "clip_selection") {
		// Request plain text so the shortcut path stays robust across frames and DOM variance
		const response = await chrome.tabs
			.sendMessage(tab.id, { type: "GET_SELECTION" })
			.catch(() => null);
		const front = response?.text?.trim() || "";
		if (!front) return;

		// Capture source metadata now so later exports keep page context
		const newCard = createCard({
			front,
			srcTitle: tab.title || "",
			srcUrl: tab.url || "",
		});
		const cards = await loadCards();
		cards.unshift(newCard);
		await saveCards(cards);
		chrome.runtime.sendMessage({
			type: "cards:created",
			payload: { id: newCard.id },
		});
	}

	if (command === "open-study-panel") {
		// Keep the secondary shortcut tiny because panel open already owns its own fallback logic
		await chrome.sidePanel.open({ windowId: tab.windowId });
	}
});

// ---------- context menu ----------

// Register the context menu on install so the selection save affordance stays discoverable
chrome.runtime.onInstalled.addListener(() => {
	chrome.contextMenus.create({
		id: "clip_save_selection",
		title: "Save selection as flashcard",
		contexts: ["selection"],
	});
});

// ---------- tab lifecycle ----------

// Keep the tab update hook reserved so later page injection work has one obvious home
chrome.tabs.onUpdated.addListener((_tabId, changeInfo, tab) => {
	if (changeInfo.status === "complete" && /^http/.test(tab.url || "")) {
		// Intentionally empty for now because page injection is not part of the bounded legacy shell
	}
});
