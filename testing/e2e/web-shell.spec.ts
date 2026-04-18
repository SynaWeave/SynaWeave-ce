/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  prove the first web-shell runtime path through sign-in workspace bootstrap durable write digest completion and browser timing capture

- Later Extension Points:
  --> add more browser journeys only when later Sprint work creates new critical runtime paths

- Role:
  --> covers the bounded D3 smoke path for the local web shell
  --> keeps the browser proof anchored to real API-backed state changes

- Exports:
  --> Playwright smoke test only

- Consumed By:
  --> `bun run test:e2e`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

import { writeFile } from "node:fs/promises";

import { expect, test } from "@playwright/test";

test("web shell signs in writes a durable action and runs a digest", async ({
	page,
}, testInfo) => {
	const stamp = Date.now();
	const email = `playwright-web-${stamp}@example.com`;
	const durableNote = `Playwright durable note ${stamp}`;

	await page.goto("/");
	const navigationTiming = await page.evaluate(() => {
		const entry = performance.getEntriesByType("navigation")[0];
		if (!(entry instanceof PerformanceNavigationTiming)) {
			return null;
		}
		return {
			domContentLoadedMs: Number(entry.domContentLoadedEventEnd.toFixed(2)),
			loadEventMs: Number(entry.loadEventEnd.toFixed(2)),
		};
	});

	await expect(
		page.getByRole("heading", { name: "SynaWeave Workspace" }),
	).toBeVisible();
	await page.getByLabel("Email").fill(email);
	const signInStartedAt = await page.evaluate(() => performance.now());
	await page.getByRole("button", { name: "Start workspace session" }).click();

	await expect(page.getByRole("heading", { name: "Workspace" })).toBeVisible();
	const workspaceReadyAt = await page.evaluate(() => performance.now());
	await expect(page.locator("#identity-email")).toHaveText(email);
	await expect(page.locator("#bridge-code")).not.toHaveText("—");
	await expect(page.locator("#workspace-id")).toContainText("wsp_");

	await page.getByLabel("Durable note").fill(durableNote);
	const actionStartedAt = await page.evaluate(() => performance.now());
	await page.getByRole("button", { name: "Write durable action" }).click();

	await expect(page.locator("#recent-actions")).toContainText(durableNote);
	const actionVisibleAt = await page.evaluate(() => performance.now());
	await expect(page.locator("#status-line")).toHaveText(
		"Durable action written through the API.",
	);

	const digestStartedAt = await page.evaluate(() => performance.now());
	await page.getByRole("button", { name: "Run digest job" }).click();

	await expect(page.locator("#last-digest")).toContainText(durableNote);
	await expect(page.locator("#latest-eval")).toContainText("digest_density");
	const digestReadyAt = await page.evaluate(() => performance.now());
	await expect(page.locator("#status-line")).toHaveText(
		"Background digest completed and reloaded.",
	);

	const timing = {
		navigationTiming,
		workspaceReadyMs: Number((workspaceReadyAt - signInStartedAt).toFixed(2)),
		actionRoundTripMs: Number((actionVisibleAt - actionStartedAt).toFixed(2)),
		digestRoundTripMs: Number((digestReadyAt - digestStartedAt).toFixed(2)),
	};

	expect(timing.workspaceReadyMs).toBeGreaterThan(0);
	expect(timing.actionRoundTripMs).toBeGreaterThan(0);
	expect(timing.digestRoundTripMs).toBeGreaterThan(0);

	await writeFile(
		testInfo.outputPath("web-shell-timing.json"),
		`${JSON.stringify(timing, null, 2)}\n`,
		"utf-8",
	);
});
