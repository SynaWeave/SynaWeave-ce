/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  define provider-neutral session shape contracts for shared cross-surface identity state

- Later Extension Points:
  --> widen session detail only when new governed assurance or continuity fields become necessary

- Role:
  --> exposes the shared session assurance vocabulary
  --> keeps session payloads stable before runtime-specific auth code begins landing

- Exports:
  --> `SESSION_LEVELS`
  --> `SessionInfo`

- Consumed By:
  --> shared auth contracts and future browser or server auth adapters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

// ---------- auth session contracts ----------
// Purpose: keep cross-surface session state serializable and provider-neutral.
export const SESSION_LEVELS = ["aal1", "aal2", "aal3"] as const;

export type SessionLevel = (typeof SESSION_LEVELS)[number];

export interface SessionInfo {
	subId: string;
	sessId: string;
	issuedAt: string;
	expiresAt: string;
	level?: SessionLevel;
}
