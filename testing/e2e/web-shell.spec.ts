/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  prove the public landing page renders as the bounded web surface and captures basic browser timing evidence

- Later Extension Points:
  --> add more public web journeys only when the landing page grows beyond one static investor-facing route

- Role:
  --> covers the bounded smoke path for the static landing page
  --> keeps one browser timing artifact for the public web surface without asserting retired auth shell behavior

- Exports:
  --> Playwright smoke test only

- Consumed By:
  --> `bun run test:e2e`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

import { writeFile } from "node:fs/promises";

import { expect, test } from "@playwright/test";

type WebVitalsEvidence = {
	cls: number;
	fcpMs: number | null;
	interactionEventCount: number;
	inpMs: number | null;
	lcpMs: number | null;
	supportedEntryTypes: string[];
};

test("public landing page presents the coming-soon investor narrative", async ({
	page,
}, testInfo) => {
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
		page.getByRole("heading", {
			name: "The learning operating system for durable knowledge work.",
		}),
	).toBeVisible();
	await expect(
		page.getByRole("heading", { level: 2, name: "What we are building" }),
	).toBeVisible();
	await expect(
		page.getByText("Public landing page • Coming soon"),
	).toBeVisible();
	await expect(
		page.getByText("Sprint 1 is live as a governed foundation."),
	).toBeVisible();
	await expect(
		page.getByRole("link", { name: "View investor snapshot" }),
	).toBeVisible();
	await expect(page.getByRole("link", { name: "Contact" })).toBeVisible();
	await expect(page.getByLabel("Investor snapshot")).toBeVisible();
	await expect(page.getByLabel("Positioning statement")).toContainText(
		"durable learning infrastructure",
	);
	await expect(page.getByLabel("Email")).toHaveCount(0);

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
			"Core Web Vitals proof is bounded to the public landing page only.",
		navigationTiming,
		webVitals,
	};

	expect(webVitals).toBeTruthy();
	if (!webVitals) {
		throw new Error(
			"Missing landing-page vitals evidence from the browser run.",
		);
	}
	expect(webVitals.lcpMs).toBeGreaterThan(0);
	expect(webVitals.cls).toBeGreaterThanOrEqual(0);
	expect(webVitals.fcpMs).toBeGreaterThan(0);
	if (
		webVitals.supportedEntryTypes.includes("event") &&
		webVitals.interactionEventCount > 0
	) {
		expect(webVitals.inpMs).toBeGreaterThan(0);
	}

	await writeFile(
		testInfo.outputPath("web-landing-page-timing.json"),
		`${JSON.stringify(timing, null, 2)}\n`,
		"utf-8",
	);
});
