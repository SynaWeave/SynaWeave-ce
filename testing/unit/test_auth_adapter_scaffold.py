"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify the provider-neutral auth scaffold stays present in shared contracts

- Later Extension Points:
    --> add more scaffold checks only when governed auth files or naming rules expand

- Role:
    --> checks the auth scaffold file set exists in the shared package boundaries
    --> blocks provider names from leaking into the shared auth contract exports

- Exports:
    --> unit test cases only

- Consumed By:
    --> Python unit test discovery during repository verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestAuthAdapterScaffold(unittest.TestCase):
    def test_auth_contract_files_exist(self):
        expected_paths = (
            REPO_ROOT / "packages/contracts/auth/methods.ts",
            REPO_ROOT / "packages/contracts/auth/session.ts",
            REPO_ROOT / "packages/contracts/auth/identity.ts",
            REPO_ROOT / "packages/contracts/auth/requests.ts",
            REPO_ROOT / "packages/contracts/auth/errors.ts",
            REPO_ROOT / "packages/contracts/auth/adapters.ts",
            REPO_ROOT / "packages/contracts/auth/index.ts",
            REPO_ROOT / "packages/config/auth/public.ts",
            REPO_ROOT / "packages/config/auth/server.ts",
        )
        for path in expected_paths:
            self.assertTrue(path.exists(), msg=f"missing auth scaffold file: {path}")

    def test_shared_auth_contracts_stay_provider_neutral(self):
        provider_names = ("google", "apple", "github", "linkedin", "supabase")
        contract_paths = (
            REPO_ROOT / "packages/contracts/auth/methods.ts",
            REPO_ROOT / "packages/contracts/auth/session.ts",
            REPO_ROOT / "packages/contracts/auth/identity.ts",
            REPO_ROOT / "packages/contracts/auth/requests.ts",
            REPO_ROOT / "packages/contracts/auth/errors.ts",
            REPO_ROOT / "packages/contracts/auth/adapters.ts",
            REPO_ROOT / "packages/contracts/auth/index.ts",
        )
        for path in contract_paths:
            text = path.read_text().lower()
            for provider_name in provider_names:
                self.assertNotIn(
                    provider_name,
                    text,
                    msg=f"provider leaked into shared contract: {path}",
                )


if __name__ == "__main__":
    unittest.main()
