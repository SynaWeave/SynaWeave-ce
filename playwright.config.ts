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
const PLAYWRIGHT_MANAGED_SERVERS =
	process.env.PLAYWRIGHT_MANAGED_SERVERS === "1";
const PLAYWRIGHT_API_PORT = process.env.PLAYWRIGHT_API_PORT || "8000";
const PLAYWRIGHT_WEB_PORT = process.env.PLAYWRIGHT_WEB_PORT || "3000";
const PLAYWRIGHT_API_BASE_URL =
	process.env.PLAYWRIGHT_API_BASE_URL ||
	`http://127.0.0.1:${PLAYWRIGHT_API_PORT}`;
const PLAYWRIGHT_BASE_URL =
	process.env.PLAYWRIGHT_BASE_URL || `http://127.0.0.1:${PLAYWRIGHT_WEB_PORT}`;
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
		baseURL: PLAYWRIGHT_BASE_URL,
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
	webServer: PLAYWRIGHT_MANAGED_SERVERS
		? undefined
		: [
				{
					command: `SYNAWAVE_WEB_BASE_URL=${PLAYWRIGHT_BASE_URL} python3 -m uvicorn apps.api.main:app --host 127.0.0.1 --port ${PLAYWRIGHT_API_PORT}`,
					url: `${PLAYWRIGHT_API_BASE_URL}/health/ready`,
					reuseExistingServer: false,
					timeout: 120_000,
				},
				{
					command: `python3 -m http.server ${PLAYWRIGHT_WEB_PORT} --directory apps/web`,
					url: PLAYWRIGHT_BASE_URL,
					reuseExistingServer: false,
					timeout: 120_000,
				},
			],
});
