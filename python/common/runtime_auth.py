"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  define lightweight auth helpers for shared browser-safe identity continuity

- Later Extension Points:
    --> replace local token helpers only when the governed auth adapter lands

- Role:
    --> normalizes email input and creates opaque local session tokens
    --> keeps the cross-surface identity path deterministic without privileged credentials

- Exports:
    --> `normalize_email()`
    --> `make_token()`
    --> `make_bridge_code()`

- Consumed By:
    --> API auth routes runtime storage and tests exercising the first D2 auth proof path
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import hashlib
import secrets


# ---------- email normalization ----------
# Keep normalization minimal so the first auth proof path stays predictable and testable.
def normalize_email(value: str) -> str:
    return value.strip().lower()


# ---------- opaque token helpers ----------
# Keep tokens random and non-derivable from email for the local proof path.
def make_token() -> str:
    return secrets.token_urlsafe(24)


# ---------- bridge code ----------
# Keep bridge codes short and deterministic so web and extension can prove shared identity.
def make_bridge_code(email: str) -> str:
    digest = hashlib.sha256(normalize_email(email).encode("utf-8")).hexdigest()
    return digest[:10].upper()
