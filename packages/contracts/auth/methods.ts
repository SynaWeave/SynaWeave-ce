/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  define provider-neutral auth method and issuer identifiers for shared contract use

- Later Extension Points:
  --> add new normalized method identifiers only when a new governed auth capability becomes product-supported

- Role:
  --> exposes shared auth method identifiers without leaking provider brands
  --> keeps issuer typing stable across browser and server auth contract consumers

- Exports:
  --> `AUTH_METHODS`
  --> `ISSUER_TYPES`

- Consumed By:
  --> shared auth contracts and future runtime adapters importing auth method types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

// ---------- auth method contracts ----------
// Purpose: keep shared auth method identifiers provider-agnostic across browser and server surfaces.
export const AUTH_METHODS = [
	"federated_oidc",
	"email_link",
	"passkey",
] as const;

export type AuthMethod = (typeof AUTH_METHODS)[number];

export const ISSUER_TYPES = ["oidc", "email", "webauthn"] as const;

export type IssuerType = (typeof ISSUER_TYPES)[number];
