/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  share the minimal Chromium extension helpers used by bounded Playwright proof flows

- Later Extension Points:
  --> widen these helpers only when more governed extension journeys need the same persistent-context setup

- Role:
  --> keeps packaged extension startup and id discovery consistent across browser proof files
  --> avoids cloning the same Chromium extension bootstrap in each spec

- Exports:
  --> extension launch helper
  --> extension id helper
  --> extension token helper

- Consumed By:
  --> `testing/e2e/*.spec.ts`
  --> `testing/accessibility/browser-surfaces.spec.ts`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

import type { BrowserContext, Page } from "@playwright/test";
import { chromium } from "@playwright/test";

export async function launchExtensionContext(userDataDir: string) {
	return chromium.launchPersistentContext(userDataDir, {
		channel: "chromium",
		headless: true,
		args: [
			"--disable-extensions-except=build/extension",
			"--load-extension=build/extension",
		],
	});
}

export async function readExtensionId(context: BrowserContext) {
	let [worker] = context.serviceWorkers();
	if (!worker) {
		worker = await context.waitForEvent("serviceworker");
	}
	return new URL(worker.url()).host;
}

export async function readExtensionToken(page: Page) {
	return page.evaluate(async () => {
		const data = await (
			window as unknown as Window & {
				chrome: {
					storage: {
						local: { get: (key: string) => Promise<Record<string, string>> };
					};
				};
			}
		).chrome.storage.local.get("synaweave.extensionToken");
		return data["synaweave.extensionToken"] || null;
	});
}
