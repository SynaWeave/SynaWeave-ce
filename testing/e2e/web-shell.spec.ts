/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  prove the first web-shell runtime path plus one assembled cross-surface identity flow through sign-in workspace bootstrap durable write digest completion and browser timing capture

- Later Extension Points:
  --> add more browser journeys only when later Sprint work creates new critical runtime paths

- Role:
  --> covers the bounded D3 smoke path for the local web shell and the stronger D2 cross-surface identity proof
  --> keeps the browser proof anchored to real API-backed state changes across web and extension surfaces

- Exports:
  --> Playwright smoke test only

- Consumed By:
  --> `bun run test:e2e`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

import { writeFile } from "node:fs/promises";

import { type Page, expect, test } from "@playwright/test";

import { launchExtensionContext, readExtensionId } from "./extension.helpers";

type WebVitalsEvidence = {
	cls: number;
	fcpMs: number | null;
	interactionEventCount: number;
	inpMs: number | null;
	lcpMs: number | null;
	supportedEntryTypes: string[];
};

type SurfaceIdentity = {
	email: string;
	bridgeCode: string;
	workspaceId: string;
};

test("web shell signs in writes a durable action and runs a digest", async ({
	page,
}, testInfo) => {
	const stamp = Date.now();
	const email = `playwright-web-${stamp}@example.com`;
	const durableNote = `Playwright durable note ${stamp}`;

	await page.addInitScript(() => {
		type BrowserWebVitalsState = {
			cls: number;
			fcpMs: number | null;
			interactionEventCount: number;
			inpMs: number | null;
			lcpMs: number | null;
			supportedEntryTypes: string[];
		};

		const supportedEntryTypes = Array.isArray(
			PerformanceObserver.supportedEntryTypes,
		)
			? [...PerformanceObserver.supportedEntryTypes]
			: [];

		const vitalsState: BrowserWebVitalsState = {
			cls: 0,
			fcpMs: null,
			interactionEventCount: 0,
			inpMs: null,
			lcpMs: null,
			supportedEntryTypes,
		};

		const observe = (
			type: string,
			handleList: (list: PerformanceObserverEntryList) => void,
			options: PerformanceObserverInit = {},
		) => {
			if (!supportedEntryTypes.includes(type)) {
				return;
			}
			const observer = new PerformanceObserver((list) => {
				handleList(list);
			});
			observer.observe({ type, buffered: true, ...options });
		};

		observe("paint", (list) => {
			for (const entry of list.getEntries()) {
				if (entry.name === "first-contentful-paint") {
					vitalsState.fcpMs = Number(entry.startTime.toFixed(2));
				}
			}
		});

		observe("largest-contentful-paint", (list) => {
			for (const entry of list.getEntries()) {
				vitalsState.lcpMs = Number(entry.startTime.toFixed(2));
			}
		});

		observe("layout-shift", (list) => {
			for (const entry of list.getEntries()) {
				const layoutShiftEntry = entry as PerformanceEntry & {
					hadRecentInput?: boolean;
					value?: number;
				};
				if (!layoutShiftEntry.hadRecentInput) {
					vitalsState.cls = Number(
						(vitalsState.cls + Number(layoutShiftEntry.value || 0)).toFixed(4),
					);
				}
			}
		});

		observe(
			"event",
			(list) => {
				for (const entry of list.getEntries()) {
					vitalsState.interactionEventCount += 1;
					const eventEntry = entry as PerformanceEntry & {
						duration: number;
					};
					vitalsState.inpMs = Math.max(
						vitalsState.inpMs || 0,
						Number(eventEntry.duration.toFixed(2)),
					);
				}
			},
			{ durationThreshold: 16 } as PerformanceObserverInit,
		);

		(
			globalThis as typeof globalThis & {
				__synaweaveWebVitals?: BrowserWebVitalsState;
			}
		).__synaweaveWebVitals = vitalsState;
	});

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

	const webVitals = await page.evaluate(
		() =>
			(
				globalThis as typeof globalThis & {
					__synaweaveWebVitals?: WebVitalsEvidence;
				}
			).__synaweaveWebVitals,
	);

	const timing = {
		browserProofLimit:
			"Core Web Vitals proof is bounded to the web shell page. Extension timing evidence is tracked separately as side-panel open and popup boot timing, not as Core Web Vitals.",
		navigationTiming,
		webVitals,
		workspaceReadyMs: Number((workspaceReadyAt - signInStartedAt).toFixed(2)),
		actionRoundTripMs: Number((actionVisibleAt - actionStartedAt).toFixed(2)),
		digestRoundTripMs: Number((digestReadyAt - digestStartedAt).toFixed(2)),
	};

	expect(webVitals).toBeTruthy();
	if (!webVitals) {
		throw new Error("Missing web-shell vitals evidence from the browser run.");
	}
	expect(webVitals.lcpMs).toBeGreaterThan(0);
	expect(webVitals.cls).toBeGreaterThanOrEqual(0);
	expect(webVitals.fcpMs).toBeGreaterThan(0);
	if (webVitals.supportedEntryTypes.includes("event")) {
		expect(webVitals.inpMs).toBeGreaterThan(0);
	}

	expect(timing.workspaceReadyMs).toBeGreaterThan(0);
	expect(timing.actionRoundTripMs).toBeGreaterThan(0);
	expect(timing.digestRoundTripMs).toBeGreaterThan(0);

	await writeFile(
		testInfo.outputPath("web-shell-timing.json"),
		`${JSON.stringify(timing, null, 2)}\n`,
		"utf-8",
	);
});

test("web and extension resolve one live user workspace and bridge identity", async ({
	browserName,
	page,
}, testInfo) => {
	expect(browserName).toBe("chromium");

	const stamp = Date.now();
	const email = `playwright-shared-identity-${stamp}@example.com`;
	const webNote = `Playwright shared web note ${stamp}`;
	const extensionNote = `Playwright shared extension note ${stamp}`;
	const context = await launchExtensionContext(
		testInfo.outputPath("extension-shared-identity-profile"),
	);

	try {
		const extensionId = await readExtensionId(context);
		const extensionPage = await context.newPage();

		await page.goto("/");
		await extensionPage.goto(`chrome-extension://${extensionId}/popup.html`);

		await page.getByLabel("Email").fill(email);
		await page.getByRole("button", { name: "Start workspace session" }).click();
		await expect(
			page.getByRole("heading", { name: "Workspace" }),
		).toBeVisible();
		await expect(page.locator("#identity-email")).toHaveText(email);
		await expect(page.locator("#bridge-code")).not.toHaveText("—");
		await expect(page.locator("#workspace-id")).toContainText("wsp_");

		await extensionPage.getByLabel("Email").fill(email);
		await extensionPage
			.getByRole("button", { name: "Connect panel session" })
			.click();
		await expect(
			extensionPage.getByRole("heading", { name: "Workspace" }),
		).toBeVisible();
		await expect(extensionPage.locator("#ext-identity-email")).toHaveText(
			email,
		);
		await expect(extensionPage.locator("#ext-bridge-code")).not.toHaveText("—");
		await expect(extensionPage.locator("#ext-workspace-id")).toContainText(
			"wsp_",
		);

		const webIdentity = await readSurfaceIdentity(page, {
			email: "#identity-email",
			bridgeCode: "#bridge-code",
			workspaceId: "#workspace-id",
		});
		const extensionIdentity = await readSurfaceIdentity(extensionPage, {
			email: "#ext-identity-email",
			bridgeCode: "#ext-bridge-code",
			workspaceId: "#ext-workspace-id",
		});

		expect(extensionIdentity).toEqual(webIdentity);

		await page.getByLabel("Durable note").fill(webNote);
		await page.getByRole("button", { name: "Write durable action" }).click();
		await expect(page.locator("#recent-actions")).toContainText(webNote);

		await extensionPage.reload();
		await expect(extensionPage.locator("#ext-recent-actions")).toContainText(
			webNote,
		);

		await extensionPage.getByLabel("Captured note").fill(extensionNote);
		await extensionPage
			.getByRole("button", { name: "Write durable action" })
			.click();
		await expect(extensionPage.locator("#ext-recent-actions")).toContainText(
			extensionNote,
		);

		await page.reload();
		await expect(page.locator("#recent-actions")).toContainText(extensionNote);

		await Promise.all([
			extensionPage.waitForResponse(
				(response) =>
					response.url().endsWith("/v1/jobs/workspace") && response.ok(),
			),
			extensionPage.getByRole("button", { name: "Run digest job" }).click(),
		]);
		await extensionPage.reload();
		await expect(extensionPage.locator("#ext-last-digest")).toContainText(
			extensionNote,
		);
		await expect(extensionPage.locator("#ext-latest-eval")).toContainText(
			"digest_density",
		);

		await page.reload();
		await expect(page.locator("#last-digest")).toContainText(extensionNote);
		await expect(page.locator("#latest-eval")).toContainText("digest_density");

		const refreshedWebIdentity = await readSurfaceIdentity(page, {
			email: "#identity-email",
			bridgeCode: "#bridge-code",
			workspaceId: "#workspace-id",
		});
		const refreshedExtensionIdentity = await readSurfaceIdentity(
			extensionPage,
			{
				email: "#ext-identity-email",
				bridgeCode: "#ext-bridge-code",
				workspaceId: "#ext-workspace-id",
			},
		);

		expect(refreshedWebIdentity).toEqual(webIdentity);
		expect(refreshedExtensionIdentity).toEqual(webIdentity);

		await writeFile(
			testInfo.outputPath("cross-surface-identity-proof.json"),
			`${JSON.stringify(
				{
					email,
					identity: webIdentity,
					proof: {
						matchedAcrossSurfaces: true,
						webActionVisibleInExtension: webNote,
						extensionActionVisibleInWeb: extensionNote,
						lastDigest: await page.locator("#last-digest").textContent(),
						latestEval: await page.locator("#latest-eval").textContent(),
					},
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

async function readSurfaceIdentity(
	page: Page,
	selectors: { email: string; bridgeCode: string; workspaceId: string },
): Promise<SurfaceIdentity> {
	return {
		email: (await page.locator(selectors.email).textContent())?.trim() || "",
		bridgeCode:
			(await page.locator(selectors.bridgeCode).textContent())?.trim() || "",
		workspaceId:
			(await page.locator(selectors.workspaceId).textContent())?.trim() || "",
	};
}
