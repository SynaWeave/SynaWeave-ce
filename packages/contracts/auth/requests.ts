/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  define normalized sign-in request and next-step contracts for shared auth flows

- Later Extension Points:
  --> add more next-step variants only when the governed auth seam supports new bounded flow kinds

- Role:
  --> exposes browser-safe sign-in request shapes and PKCE payload structure
  --> keeps sign-in flow responses normalized before provider adapters are implemented

- Exports:
  --> `SignInStartReq`
  --> `SignInStartRes`
  --> related sign-in step contracts

- Consumed By:
  --> future browser auth adapters and API-facing auth flow orchestration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

// ---------- auth request contracts ----------
// Purpose: keep browser and server auth request shapes stable before runtime adapters are filled in.
import type { AuthMethod } from "./methods.js";

export interface PkceState {
	codeChallenge: string;
	codeChallengeMethod: "S256";
}

export interface SignInStartReq {
	method: AuthMethod;
	connHint?: string;
	redirectUri: string;
	pkce?: PkceState;
	loginHint?: string;
}

export interface RedirectStep {
	kind: "redirect";
	url: string;
}

export interface EmailStep {
	kind: "email_sent";
}

export interface WebAuthnCreateStep {
	kind: "webauthn_create";
	publicKey: unknown;
}

export interface WebAuthnGetStep {
	kind: "webauthn_get";
	publicKey: unknown;
}

export type SignInNextStep =
	| RedirectStep
	| EmailStep
	| WebAuthnCreateStep
	| WebAuthnGetStep;

export interface SignInStartRes {
	flowId: string;
	nextStep: SignInNextStep;
}
