/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  define unbranded browser and server adapter interfaces for future auth implementations

- Later Extension Points:
  --> add more adapter methods only when a new governed auth capability needs a stable shared seam

- Role:
  --> exposes the browser-side and server-side auth adapter contracts
  --> keeps provider-specific implementations behind stable shared interfaces from the start

- Exports:
  --> `BrowserAuthAdapter`
  --> `ServerAuthAdapter`

- Consumed By:
  --> future auth runtime implementations under package and app boundaries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

import type { VerifiedIdentity } from "./identity.js";
// ---------- auth adapter contracts ----------
// Purpose: keep runtime adapters unbranded so provider swaps stay isolated at the edge.
import type { SignInStartReq, SignInStartRes } from "./requests.js";
import type { SessionInfo } from "./session.js";

export interface BrowserAuthAdapter {
	startSignIn(input: SignInStartReq): Promise<SignInStartRes>;
	getSession(): Promise<SessionInfo | null>;
	signOut(): Promise<void>;
}

export interface ServerAuthAdapter {
	verifySession(input: {
		accessToken?: string;
		idToken?: string;
	}): Promise<VerifiedIdentity>;
}
