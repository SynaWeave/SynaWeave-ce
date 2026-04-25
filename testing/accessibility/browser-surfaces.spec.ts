/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  run automated accessibility smoke checks for the public landing page and the packaged extension panel document

- Later Extension Points:
  --> add richer panel-container automation only when the repo owns a stable Chromium side-panel harness

- Role:
  --> proves Axe coverage for the public web landing page
  --> scans the built extension panel document without inventing a larger browser harness

- Exports:
  --> Playwright accessibility tests only

- Consumed By:
  --> `bun run test:accessibility`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import {
	launchExtensionContext,
	prepareExtensionApiBase,
	readExtensionId,
} from "../e2e/extension.helpers";

test("public landing page has no automated accessibility violations", async ({
	page,
}) => {
	await page.goto("/");
	await expect(
		page.getByRole("heading", {
			name: "The learning operating system for durable knowledge work.",
		}),
	).toBeVisible();

	const results = await new AxeBuilder({ page }).analyze();

	expect(results.violations).toEqual([]);
});

test("packaged extension panel document has no automated accessibility violations", async ({
	browserName,
}, testInfo) => {
	expect(browserName).toBe("chromium");

	const context = await launchExtensionContext(
		testInfo.outputPath("extension-profile"),
	);

	try {
		const extensionId = await readExtensionId(context);
		const page = await context.newPage();
		const email = `playwright-a11y-ext-${Date.now()}@example.com`;

		await page.goto(`chrome-extension://${extensionId}/popup.html`);
		await prepareExtensionApiBase(page);
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
