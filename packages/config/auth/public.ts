/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  define browser-safe auth configuration contracts for future client runtime use

- Later Extension Points:
  --> add more browser-safe config fields only when governed client auth flows require them

- Role:
  --> exposes the public auth configuration shape for browser surfaces
  --> keeps browser-safe auth settings separated from privileged verification config

- Exports:
  --> `PublicAuthCfg`

- Consumed By:
  --> future web and extension auth configuration loaders
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

// ---------- public auth config ----------
// Purpose: keep browser-safe auth settings separate from privileged server-only configuration.
import type { AuthMethod } from "../../contracts/auth/methods.js";

export interface PublicAuthCfg {
	baseUrl: string;
	redirectBaseUrl: string;
	methods: AuthMethod[];
	connMap: Record<string, string>;
	pkce: true;
	passwords: false;
}
