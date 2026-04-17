/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  define server-only auth configuration contracts for future verification adapter use

- Later Extension Points:
  --> add more privileged config fields only when backend auth verification grows beyond the current seam

- Role:
  --> exposes the server-only auth configuration shape
  --> keeps privileged issuer and verification settings out of browser-safe config surfaces

- Exports:
  --> `ServerAuthCfg`

- Consumed By:
  --> future API and job auth verification adapters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

// ---------- server auth config ----------
// Purpose: keep privileged auth verification and issuer mapping settings on the server boundary only.
export interface ServerAuthCfg {
	issuerUrl: string;
	audience: string;
	jwksUrl: string;
	serviceRoleEnv: string;
	connMap: Record<string, string>;
	allowPasswordAuth: false;
}
