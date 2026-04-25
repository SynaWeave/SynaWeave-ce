/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  prove degraded-mode browser behavior for the extension popup now that the web surface is a static landing page

- Later Extension Points:
  --> widen degraded checks only when later runtime paths add more retryable browser-owned failure states

- Role:
  --> covers extension bootstrap telemetry plus invalid-auth recovery without claiming side-panel container DOM inspection
  --> removes retired web-shell degraded assertions that no longer match the public landing page

- Exports:
  --> Playwright smoke test only

- Consumed By:
  --> `bun run test:e2e`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

import { type BrowserContext, type Page, expect, test } from "@playwright/test";

import {
	PLAYWRIGHT_API_BASE_URL,
	launchExtensionContext,
	prepareExtensionApiBase,
	readExtensionId,
	readExtensionToken,
} from "./extension.helpers";

const API_BASE_URL = PLAYWRIGHT_API_BASE_URL;
const TRANSIENT_ERROR_MESSAGE =
	"Temporary API or provider failure. Session kept so you can retry.";

type TelemetryPayload = {
	surface: string;
	name: string;
	status: string;
	detail: string;
};

test("extension popup keeps the stored session through transient bootstrap failures and clears invalid auth", async ({
	browserName,
}, testInfo) => {
	expect(browserName).toBe("chromium");

	const context = await launchExtensionContext(
		testInfo.outputPath("extension-degraded-profile"),
	);
	const telemetry = await collectTelemetry(context);

	try {
		const extensionId = await readExtensionId(context);
		const page = await context.newPage();
		const email = `playwright-extension-degraded-${Date.now()}@example.com`;

		await page.goto(`chrome-extension://${extensionId}/popup.html`);
		await prepareExtensionApiBase(page);
		await page.getByLabel("Email").fill(email);
		await page.getByRole("button", { name: "Connect panel session" }).click();
		await expect(page.locator("#ext-identity-email")).toHaveText(email);

		let blockBootstrap = true;
		await context.route(`${API_BASE_URL}/v1/workspace/bootstrap`, (route) => {
			if (blockBootstrap) {
				return route.fulfill({
					status: 503,
					contentType: "application/json",
					body: JSON.stringify({ detail: "provider timeout" }),
				});
			}
			return route.continue();
		});

		await page.reload();
		await expect(page.locator("#workspace-section")).toBeVisible();
		await expect(page.locator("#ext-degraded-card")).toBeVisible();
		await expect(page.locator("#panel-status-line")).toHaveText(
			TRANSIENT_ERROR_MESSAGE,
		);
		expect(await readExtensionToken(page)).toBeTruthy();
		await expectTelemetry(telemetry, "extension_workspace_bootstrap", {
			status: "degraded",
			detailParts: [
				"kind=transient",
				"retryable=true",
				"status=503",
				"message=provider timeout",
			],
		});

		blockBootstrap = false;
		await page
			.getByRole("button", { name: "Retry the workspace refresh" })
			.click();
		await expect(page.locator("#panel-status-line")).toHaveText(
			`Extension workspace ready for ${email}.`,
		);
		await expect(page.locator("#ext-degraded-card")).toBeHidden();

		await context.route(`${API_BASE_URL}/v1/identity`, (route) =>
			route.fulfill({
				status: 401,
				contentType: "application/json",
				body: JSON.stringify({ detail: "session invalid" }),
			}),
		);
		await page.reload();
		await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
		await expect(page.locator("#workspace-section")).toBeHidden();
		await expect(page.locator("#ext-degraded-card")).toBeHidden();
		await expect(page.locator("#panel-status-line")).toHaveText(
			"Stored extension session expired or was invalid, so the panel returned to signed-out state.",
		);
		expect(await readExtensionToken(page)).toBeNull();
		await expectTelemetry(telemetry, "extension_workspace_bootstrap", {
			status: "error",
			detailParts: [
				"kind=auth",
				"retryable=false",
				"status=401",
				"message=session invalid",
			],
		});
	} finally {
		await context.close();
	}
});

async function collectTelemetry(target: Page | BrowserContext) {
	const events: TelemetryPayload[] = [];
	await target.route(`${API_BASE_URL}/v1/telemetry/emit`, async (route) => {
		events.push(route.request().postDataJSON() as TelemetryPayload);
		await route.fulfill({
			status: 200,
			contentType: "application/json",
			body: JSON.stringify({
				status: "accepted",
				meta: {},
				payload: { accepted: true },
			}),
		});
	});
	return events;
}

async function expectTelemetry(
	events: TelemetryPayload[],
	name: string,
	options: { status: string; detailParts: string[] },
) {
	await expect
		.poll(() =>
			events.filter(
				(event) =>
					event.name === name &&
					event.status === options.status &&
					options.detailParts.every((part) => event.detail.includes(part)),
			),
		)
		.toHaveLength(1);
}
