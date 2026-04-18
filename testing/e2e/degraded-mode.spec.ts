/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  prove degraded-mode browser behavior keeps retryable sessions alive while invalid auth still signs the operator out

- Later Extension Points:
  --> widen degraded checks only when later runtime paths add more retryable browser-owned failure states

- Role:
  --> covers degraded bootstrap and action or job retry behavior for the web shell
  --> covers extension bootstrap telemetry plus invalid-auth recovery without claiming side-panel container DOM inspection

- Exports:
  --> Playwright smoke test only

- Consumed By:
  --> `bun run test:e2e`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

import {
	type BrowserContext,
	type Page,
	chromium,
	expect,
	test,
} from "@playwright/test";

const API_BASE_URL = "http://127.0.0.1:8000";
const TRANSIENT_ERROR_MESSAGE =
	"Temporary API or provider failure. Session kept so you can retry.";

type TelemetryPayload = {
	surface: string;
	name: string;
	status: string;
	detail: string;
};

test("web shell keeps the session through transient bootstrap failures and clears it for invalid auth", async ({
	page,
}) => {
	const telemetry = await collectTelemetry(page);
	const stamp = Date.now();
	const email = `playwright-web-degraded-${stamp}@example.com`;

	await page.goto("/");
	await page.getByLabel("Email").fill(email);
	await page.getByRole("button", { name: "Start workspace session" }).click();
	await expect(page.locator("#identity-email")).toHaveText(email);

	let blockBootstrap = true;
	await page.route(`${API_BASE_URL}/v1/workspace/bootstrap`, (route) => {
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
	await expect(page.getByRole("heading", { name: "Workspace" })).toBeVisible();
	await expect(page.locator("#degraded-card")).toBeVisible();
	await expect(page.locator("#status-line")).toHaveText(
		TRANSIENT_ERROR_MESSAGE,
	);
	await expect(page.locator("#retry-button")).toHaveText(
		"Retry the workspace refresh",
	);
	expect(await readWebToken(page)).toBeTruthy();
	await expectTelemetry(telemetry, "web_workspace_bootstrap", {
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
	await expect(page.locator("#status-line")).toHaveText(
		`Workspace ready for ${email}.`,
	);
	await expect(page.locator("#degraded-card")).toBeHidden();

	await page.route(`${API_BASE_URL}/v1/identity`, (route) =>
		route.fulfill({
			status: 401,
			contentType: "application/json",
			body: JSON.stringify({ detail: "session invalid" }),
		}),
	);
	await page.reload();
	await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
	await expect(page.locator("#workspace-card")).toBeHidden();
	await expect(page.locator("#degraded-card")).toBeHidden();
	await expect(page.locator("#status-line")).toHaveText(
		"Stored session expired or was invalid, so the web shell returned to signed-out state.",
	);
	expect(await readWebToken(page)).toBeNull();
	await expectTelemetry(telemetry, "web_workspace_bootstrap", {
		status: "error",
		detailParts: [
			"kind=auth",
			"retryable=false",
			"status=401",
			"message=session invalid",
		],
	});
});

test("web shell retries action and digest requests after transient failures", async ({
	page,
}) => {
	const telemetry = await collectTelemetry(page);
	const stamp = Date.now();
	const email = `playwright-web-retry-${stamp}@example.com`;
	const durableNote = `Playwright retry note ${stamp}`;

	await page.goto("/");
	await page.getByLabel("Email").fill(email);
	await page.getByRole("button", { name: "Start workspace session" }).click();
	await expect(page.locator("#identity-email")).toHaveText(email);

	let failActionOnce = true;
	await page.route(`${API_BASE_URL}/v1/workspace/action`, (route) => {
		if (failActionOnce) {
			failActionOnce = false;
			return route.fulfill({
				status: 503,
				contentType: "application/json",
				body: JSON.stringify({ detail: "provider timeout" }),
			});
		}
		return route.continue();
	});

	await page.getByLabel("Durable note").fill(durableNote);
	await page.getByRole("button", { name: "Write durable action" }).click();
	await expect(page.locator("#degraded-card")).toBeVisible();
	await expect(page.locator("#retry-button")).toHaveText(
		"Retry the durable action write",
	);
	await expect(page.locator("#action-input")).toHaveValue(durableNote);
	expect(await readWebToken(page)).toBeTruthy();
	await expectTelemetry(telemetry, "web_action_write", {
		status: "degraded",
		detailParts: [
			"kind=transient",
			"retryable=true",
			"status=503",
			"message=provider timeout",
		],
	});

	await page
		.getByRole("button", { name: "Retry the durable action write" })
		.click();
	await expect(page.locator("#status-line")).toHaveText(
		"Durable action written through the API.",
	);
	await expect(page.locator("#degraded-card")).toBeHidden();
	await expect(page.locator("#action-input")).toHaveValue("");
	await expect(page.locator("#recent-actions")).toContainText(durableNote);

	let failJobOnce = true;
	await page.route(`${API_BASE_URL}/v1/jobs/workspace`, (route) => {
		if (failJobOnce) {
			failJobOnce = false;
			return route.fulfill({
				status: 502,
				contentType: "application/json",
				body: JSON.stringify({ detail: "job provider timeout" }),
			});
		}
		return route.continue();
	});

	await page.getByRole("button", { name: "Run digest job" }).click();
	await expect(page.locator("#degraded-card")).toBeVisible();
	await expect(page.locator("#retry-button")).toHaveText(
		"Retry the digest job",
	);
	await expectTelemetry(telemetry, "web_digest_run", {
		status: "degraded",
		detailParts: [
			"kind=transient",
			"retryable=true",
			"status=502",
			"message=job provider timeout",
		],
	});

	await page.getByRole("button", { name: "Retry the digest job" }).click();
	await expect(page.locator("#status-line")).toHaveText(
		"Background digest completed and reloaded.",
	);
	await expect(page.locator("#degraded-card")).toBeHidden();
	await expect(page.locator("#last-digest")).toContainText(durableNote);
});

test("extension popup keeps the stored session through transient bootstrap failures and clears invalid auth", async ({
	browserName,
}, testInfo) => {
	expect(browserName).toBe("chromium");

	const context = await chromium.launchPersistentContext(
		testInfo.outputPath("extension-degraded-profile"),
		{
			channel: "chromium",
			headless: true,
			args: [
				"--disable-extensions-except=build/extension",
				"--load-extension=build/extension",
			],
		},
	);
	const telemetry = await collectTelemetry(context);

	try {
		const extensionId = await readExtensionId(context);
		const page = await context.newPage();
		const email = `playwright-extension-degraded-${Date.now()}@example.com`;

		await page.goto(`chrome-extension://${extensionId}/popup.html`);
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

async function readWebToken(page: Page) {
	return page.evaluate(() => localStorage.getItem("synaweave.webToken"));
}

async function readExtensionId(context: BrowserContext) {
	let [worker] = context.serviceWorkers();
	if (!worker) {
		worker = await context.waitForEvent("serviceworker");
	}
	return new URL(worker.url()).host;
}

async function readExtensionToken(page: Page) {
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
