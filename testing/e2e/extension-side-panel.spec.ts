/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  prove the closest real Chromium side-panel path by opening the browser-owned container from an extension harness

- Later Extension Points:
  --> replace storage-based runtime evidence only when Playwright can inspect the actual side-panel container DOM directly

- Role:
  --> uses an actual extension page click to trigger `chrome.sidePanel.open()` under Chromium gesture rules
  --> captures side-panel timing evidence without claiming DOM-level container inspection that Playwright still cannot provide here

- Exports:
  --> Playwright smoke test only

- Consumed By:
  --> `bun run test:e2e`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

import { writeFile } from "node:fs/promises";

import { expect, test } from "@playwright/test";

import { launchExtensionContext, readExtensionId } from "./extension.helpers";

type PanelEvidence = {
	href: string;
	openToBootMs: number;
	panelSurfaceReadyMs: number;
	requestedAt: number;
	bootedAt: number;
	requestAgeMs: number | null;
	documentReadyState: string;
};

test("extension harness opens the browser-owned side panel and records runtime timing", async ({
	browserName,
}, testInfo) => {
	expect(browserName).toBe("chromium");

	const context = await launchExtensionContext(
		testInfo.outputPath("extension-profile"),
	);

	try {
		const extensionId = await readExtensionId(context);
		const page = await context.newPage();

		await page.goto(`chrome-extension://${extensionId}/options.html`);
		await expect(
			page.getByRole("button", { name: "Open SynaWeave side panel" }),
		).toBeVisible();

		await page
			.getByRole("button", { name: "Open SynaWeave side panel" })
			.click();
		await expect(page.locator("#options-status-line")).toContainText(
			"Side panel opened and reported popup runtime boot",
		);

		const panelEvidence = await page.evaluate(
			() =>
				(
					window as Window & {
						__synaweaveOptionsPanelEvidence?: PanelEvidence;
					}
				).__synaweaveOptionsPanelEvidence,
		);

		expect(panelEvidence).toBeTruthy();
		if (!panelEvidence) {
			throw new Error(
				"Missing side-panel runtime evidence from the extension harness.",
			);
		}
		expect(panelEvidence.href).toContain("/popup.html");
		expect(panelEvidence.openToBootMs).toBeGreaterThanOrEqual(0);
		expect(panelEvidence.panelSurfaceReadyMs).toBeGreaterThan(0);

		await writeFile(
			testInfo.outputPath("extension-side-panel-timing.json"),
			`${JSON.stringify(
				{
					browserProofLimit:
						"Playwright proved the real side-panel open request and popup runtime boot, but it still did not inspect the browser-owned side-panel container DOM directly.",
					extensionId,
					statusLine: await page.locator("#options-status-line").textContent(),
					timing: panelEvidence,
				},
				null,
				2,
			)}\n`,
			"utf-8",
		);
	} finally {
		await context.close();
	}
});
