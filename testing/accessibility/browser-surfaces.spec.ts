/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  run automated accessibility smoke checks for the signed-in web shell and the packaged extension panel document

- Later Extension Points:
  --> add richer panel-container automation only when the repo owns a stable Chromium side-panel harness

- Role:
  --> proves Axe coverage for the local web runtime path
  --> scans the built extension panel document without inventing a larger browser harness

- Exports:
  --> Playwright accessibility tests only

- Consumed By:
  --> `bun run test:accessibility`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

import AxeBuilder from "@axe-core/playwright";
import { chromium, expect, test } from "@playwright/test";

test("signed-in web shell has no automated accessibility violations", async ({
	page,
}) => {
	const email = `playwright-a11y-web-${Date.now()}@example.com`;

	await page.goto("/");
	await page.getByLabel("Email").fill(email);
	await page.getByRole("button", { name: "Start workspace session" }).click();
	await expect(page.getByRole("heading", { name: "Workspace" })).toBeVisible();

	const results = await new AxeBuilder({ page }).analyze();

	expect(results.violations).toEqual([]);
});

test("packaged extension panel document has no automated accessibility violations", async ({
	browserName,
}, testInfo) => {
	expect(browserName).toBe("chromium");

	const context = await chromium.launchPersistentContext(
		testInfo.outputPath("extension-profile"),
		{
			channel: "chromium",
			headless: true,
			args: [
				"--disable-extensions-except=build/extension",
				"--load-extension=build/extension",
			],
		},
	);

	try {
		let [worker] = context.serviceWorkers();
		if (!worker) {
			worker = await context.waitForEvent("serviceworker");
		}

		const extensionId = new URL(worker.url()).host;
		const page = await context.newPage();
		const email = `playwright-a11y-ext-${Date.now()}@example.com`;

		await page.goto(`chrome-extension://${extensionId}/popup.html`);
		await page.getByLabel("Email").fill(email);
		await page.getByRole("button", { name: "Connect panel session" }).click();
		await expect(
			page.getByRole("heading", { name: "Workspace" }),
		).toBeVisible();

		const results = await new AxeBuilder({ page }).analyze();

		expect(results.violations).toEqual([]);
	} finally {
		await context.close();
	}
});
