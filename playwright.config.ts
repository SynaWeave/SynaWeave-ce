/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  run the bounded local browser and accessibility proof against the Sprint 1 web and extension shells

- Later Extension Points:
  --> widen projects only when more governed browser surfaces need repeatable runtime proof

- Role:
  --> starts the local API and static web shell for Playwright execution
  --> keeps browser checks deterministic and scoped to the current Sprint 1 path

- Exports:
  --> default Playwright config

- Consumed By:
  --> `bun run test:e2e`
  --> `bun run test:accessibility`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

import { defineConfig } from "@playwright/test";

const CHROMIUM_EXECUTABLE_PATH =
	process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || process.env.CHROMIUM_BIN;
const PLAYWRIGHT_HEADLESS = process.env.PLAYWRIGHT_HEADLESS !== "false";
const CHROMIUM_LAUNCH_ARGS =
	process.platform === "linux"
		? ["--no-sandbox", "--disable-dev-shm-usage"]
		: [];

export default defineConfig({
	testDir: "./testing",
	testMatch: "**/*.spec.ts",
	fullyParallel: false,
	workers: 1,
	timeout: 45_000,
	expect: {
		timeout: 10_000,
	},
	reporter: [["list"]],
	use: {
		baseURL: "http://127.0.0.1:3000",
		headless: PLAYWRIGHT_HEADLESS,
		launchOptions: {
			...(CHROMIUM_EXECUTABLE_PATH
				? { executablePath: CHROMIUM_EXECUTABLE_PATH }
				: {}),
			args: CHROMIUM_LAUNCH_ARGS,
		},
		screenshot: "only-on-failure",
		trace: "retain-on-failure",
		video: "off",
	},
	webServer: [
		{
			command:
				"python3 -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000",
			url: "http://127.0.0.1:8000/health/ready",
			reuseExistingServer: true,
			timeout: 120_000,
		},
		{
			command: "python3 -m http.server 3000 --directory apps/web",
			url: "http://127.0.0.1:3000",
			reuseExistingServer: true,
			timeout: 120_000,
		},
	],
});
