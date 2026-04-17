/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  define normalized authentication failure codes before provider adapters map native errors

- Later Extension Points:
  --> add new normalized error codes only when new governed auth failure classes become durable

- Role:
  --> exposes shared auth error codes and a bounded error envelope
  --> keeps provider-native failures from leaking into shared contract surfaces

- Exports:
  --> `AUTH_ERROR_CODES`
  --> `AuthError`

- Consumed By:
  --> future browser and server auth adapters mapping runtime-specific failures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

// ---------- auth error contracts ----------
// Purpose: keep cross-surface auth failures normalized before provider adapters map their native errors.
export const AUTH_ERROR_CODES = [
	"auth_unavailable",
	"invalid_request",
	"session_missing",
	"session_invalid",
	"session_expired",
	"identity_unverified",
	"method_not_allowed",
	"redirect_mismatch",
	"state_mismatch",
	"nonce_mismatch",
] as const;

export type AuthErrorCode = (typeof AUTH_ERROR_CODES)[number];

export interface AuthError {
	code: AuthErrorCode;
	msg: string;
	retryable?: boolean;
}
