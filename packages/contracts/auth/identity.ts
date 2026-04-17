/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  define normalized identity and linked connection shapes for verified shared auth state

- Later Extension Points:
  --> add more normalized identity fields only when they are durable cross-surface requirements

- Role:
  --> exposes provider-neutral user profile and connection shapes
  --> keeps verified identity payloads stable across future browser and server auth flows

- Exports:
  --> `IdentityProfile`
  --> `IdentityConn`
  --> `VerifiedIdentity`

- Consumed By:
  --> shared auth requests adapters and future verified session consumers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

// ---------- auth identity contracts ----------
// Purpose: keep normalized user identity and linked sign-in methods out of provider-specific shapes.
import type { AuthMethod, IssuerType } from "./methods.js";
import type { SessionInfo } from "./session.js";

export interface IdentityProfile {
	subId: string;
	primaryEmail?: string;
	displayName?: string;
	avatarUrl?: string;
}

export interface IdentityConn {
	connId: string;
	method: AuthMethod;
	issuerType: IssuerType;
	connectedAt: string;
}

export interface VerifiedIdentity {
	session: SessionInfo;
	profile: IdentityProfile;
	connections: IdentityConn[];
}
