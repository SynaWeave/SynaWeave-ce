# Security

## Security reporting

Report suspected vulnerabilities via private communication to the repository owners.

Use this minimum report format:

- impact surface
- affected component (`apps`, `packages`, `python`, `infra`, `tools`)
- reproduction steps
- suspected severity
- temporary mitigations if available

## Scope and response

- secrets found in history or PRs are reviewed immediately
- dependency risks discovered by hosted dependency review are remediated before merge when GitHub dependency graph support is available
- contract or auth boundary leaks are treated as high-priority defects

## Safe handling rules

- never commit `.env`, credentials, or provider service tokens
- keep privileged keys in deployment environments only
- validate all new dependencies against project policy

## Verification obligations

Security posture for repository changes is visible through:

- `python3 -m tools.verify.main`
- `python3 -m tools.security.betterleaks --mode staged`
- `python3 -m tools.security.betterleaks --mode tracked --include-built-extension`
- dependency review workflows in `.github/workflows/`
- Betterleaks fast secret-scanning in local hooks and fast CI
- TruffleHog deep secret-scanning in CI for git history and shipped extension artifacts
- GitHub-side secret scanning and push protection when those repository features are enabled
- contract and boundary checks in docs and ADR updates

## Secret-scanning responsibility split

- Betterleaks owns fast leak blocking in local hooks and fast CI
- TruffleHog owns the deeper CI pass across git history and built ship-facing artifacts
- the custom repo verifier owns repo-specific policy checks that generic scanners cannot model safely

Fast scanning scope starts from the tracked-file boundary.

- local and fast CI Betterleaks gates scan tracked repo files plus built extension artifacts
- local tracked-mode Betterleaks may reuse a git-local cache for unchanged clean tracked files, but config or Betterleaks version changes invalidate that cache and built extension artifacts still scan every tracked run
- gitignored cache and dependency paths do not define the trusted source surface
- the custom security verifier parses `.gitignore` to confirm env-file ignore policy and reject any tracked env drift outside the example exception

## Tightened tracked-file policy

- tracked env files are forbidden unless the path matches the reviewed `.env.example` exception from `.gitignore`
- tracked private key and secret-store formats are forbidden including `.pem`, `.key`, `.p8`, `.p12`, `.pkcs12`, `.pfx`, `.jks`, `.keystore`, and `.kdbx`
- public certificate-only formats are not blanket-banned because they can be legitimate non-secret material, so scanners still cover them instead of a hard path ban
- archive-style leak discovery is tightened through Betterleaks archive scanning in fast gates and TruffleHog artifact and history scanning in deep CI

## Repo-wide security rule

- treat all tracked files as leak-sensitive even before code reaches GitHub
- treat ship-facing artifacts as separate security surfaces that must be scanned after build steps run
- keep source comments docs examples and config placeholders non-sensitive at all times
- do not rely on GitHub or org-level security features as the first or only enforcement layer

## GitHub security control posture

The expected GitHub-side security baseline for the default branch is:

- required checks block merge when security-sensitive workflows fail
- the `dependency-review` workflow runs on pull requests and must say when hosted review is unavailable because dependency graph support is not enabled
- CodeQL remains enabled for code scanning
- secret scanning and push protection stay enabled where the repository tier supports them
- admin bypass remains exceptional and must be documented in the pull request record when used
