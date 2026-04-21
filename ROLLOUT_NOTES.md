# SynaWave Qodo + Workflow + Onboarding rollout

Included files:
- `.pr_agent.toml`
- `README.md`
- `CONTRIBUTING.md`
- `GOVERNANCE.md`
- `docs/workflow.md`
- `docs/onboarding.md`

Intent:
- keep one canonical repo workflow doc
- keep one dedicated onboarding doc for new developers
- avoid a Qodo-only policy doc
- keep Qodo configuration thin and repo-owned
- point Qodo back to the canonical docs for repo standards

Suggested rollout order:
1. Merge the docs and `.pr_agent.toml`.
2. Install Qodo GitHub integration in advisory mode.
3. Enable automatic review for PRs.
4. Copy the repo rules from the canonical docs into the Qodo portal rule system.
5. Pilot for 2-3 weeks before deciding whether to elevate severity or required status.
