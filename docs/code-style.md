# 📜 Code style

## 🧩 Purpose

This document defines the required comment contract for governed code config and workflow files in the repository.

This file is the source of truth for:

- the mandatory TL;DR header shape for covered Python, TypeScript, JavaScript, YAML, TOML, shell, and dotenv files
- the governed CSS header shape and the manual HTML note-block exception
- which files must carry the header now
- how file-level and local intent comments stay DRY and readable
- why suppressions and ignore directives are banned in governed source and config files
- what comment syntax is allowed for the TL;DR block and what is forbidden outside it

This file does **not** define sprint execution, package ownership, or workflow purpose. Those belong in:

- `docs/planning/MASTER.md`
- `docs/packages.md`
- `docs/testing.md`
- `docs/templates.md`

---

## 🧭 Code-style thesis

Every governed comment-capable file must explain itself at the top before real implementation begins.

The top-of-file TL;DR is mandatory because it:

- keeps intent reviewable before readers inspect implementation detail
- gives build agents and reviewers one stable summary shape across languages
- forces exports, role, and extension seams to stay explicit
- prevents silent growth of hidden policy logic in scripts and workflow files

All later comments must stay one physical line per intent.

That means local comments may preserve one boundary, one invariant, one warning, one reason, one section label, or one non-obvious implementation note at a time.

Keep local comments note-taking shaped.

Prefer short precise fragments over polished prose.

Explain what the nearby line or group does.

Explain why that strategy stays in place when the reason is not obvious from code alone.

The TL;DR block is the only place where file-level theory may span multiple lines.

Suppressions are banned across governed source and config surfaces.

That includes inline ignore directives and repo-level config escapes that hide warnings or type issues instead of fixing them.

---

## 📦 Covered file families now

The enforced TL;DR header currently applies to:

- `tools/**/*.py`
- `testing/**/*.py`
- `python/**/*.py`
- `packages/**/*.ts`
- `apps/**/*.js`
- `tools/**/*.ts`
- `.github/workflows/*.{yml,yaml}`
- `pyproject.toml`
- `tools/hooks/*`
- `.env.example`
- `apps/**/*.css`

The repo may widen this later, but these are the governed surfaces enforced now.

---

## 🧱 Required TL;DR sections

Every covered file must include these markers in this exact order:

1. `TL;DR  -->`
2. `- Later Extension Points:`
3. `- Role:`
4. `- Exports:`
5. `- Consumed By:`

Each section after `TL;DR  -->` must include at least one `-->` detail line.

The header must appear at the top of the file before imports, declarations, or workflow keys.

Outside the TL;DR block, comments must remain single-line and atomic.

The verifier enforces the structural part of this rule by rejecting extra multiline comment forms outside the TL;DR block for covered families that support them.

Reviewers still enforce whether a single-line comment really carries one intent instead of hidden prose.

All covered families reuse `docs/templates/code-tldr.md`.

HTML files still follow the note-taking style, but the repo keeps them note-block-governed instead of TL;DR-enforced because literal `TL;DR  -->` markers conflict with HTML comment closing syntax.

HTML comments are source-only notes.

They must never carry secrets, internal-only attack notes, credentials, tokens, or other sensitive theory.

Production HTML artifacts must strip all comments before shipping.

---

## 🐍 Python header rules

Python files must use a single module-level triple-quoted TL;DR block at the top of the file.

Rules:

- the TL;DR block is the only allowed top-level triple-quoted comment block in the file
- the file body must begin after the header block closes
- later local explanation must use one-line `#` comments only
- shebang lines are allowed before the header only where required

---

## 🟦 TypeScript header rules

TypeScript files must use a single top-of-file block-comment TL;DR block.

Rules:

- the TL;DR block is the only allowed file-scope `/* ... */` comment block
- implementation begins after the header closes
- future explanation outside the header must use one-line `//` comments only where needed

---

## 🟨 JavaScript header rules

JavaScript files must use a single top-of-file block-comment TL;DR block.

Rules:

- the TL;DR block is the only allowed file-scope `/* ... */` comment block
- implementation begins after the header closes
- future explanation outside the header must use one-line `//` comments only where needed

---

## 🟪 CSS header rules

CSS files under policy must use a top-of-file block-comment TL;DR block with the same wrapper rows used by TypeScript and JavaScript.

Rules:

- the TL;DR block must appear before selectors or variable declarations
- later CSS comments may still use `/* ... */` because CSS has no line-comment syntax
- each later CSS comment must stay on one physical line and carry one local intent only
- commented-out CSS rules are banned because they dilute active style theory

---

## 🟫 YAML header rules

YAML files must use a leading `#` comment TL;DR block.

Rules:

- the TL;DR comment block must appear before keys like `name:`, `on:`, or `jobs:`
- each required section must appear in normalized comment text
- workflow bodies may still contain regular YAML comments after the header where necessary
- each later YAML comment line must carry one local intent only

---

## 🟫 TOML header rules

TOML files under policy must use a leading `#` comment TL;DR block.

Rules:

- the TL;DR comment block must appear before TOML tables or keys
- each required section must appear in normalized comment text
- later TOML comments may exist only as one-line local intent comments

---

## ⬛ Shell header rules

Shell hook files under policy must keep the shebang first and place the TL;DR block immediately after it.

Rules:

- the shebang may appear before the TL;DR block when the runtime requires it
- the TL;DR comment block must appear before shell commands like `set`, variable declarations, or hook logic
- later shell comments may exist only as one-line local intent comments

---

## 🟩 Dotenv header rules

Dotenv example files under policy must use a leading `#` comment TL;DR block.

Rules:

- the TL;DR comment block must appear before variable assignments
- each required section must appear in normalized comment text
- later dotenv comments may exist only as one-line local intent comments

---

## 🟥 HTML source note rules

HTML may use comment-heavy source notes in development.

Rules:

- place the source note block after `<!DOCTYPE html>`
- keep each HTML comment line brief and specific
- treat HTML comments as source-only guidance, not a place for sensitive theory
- strip all HTML comments from shipped artifacts
- never place secrets, tokens, private URLs, credentials, or internal-only security notes in HTML comments

---

## 🚫 Forbidden drift

Covered files must not:

- omit the TL;DR block entirely
- reorder the required TL;DR sections
- use provider- or tool-specific block-comment formats that bypass the canonical layout
- add extra top-level Python triple-quoted comment blocks
- add extra file-scope TypeScript or JavaScript block comments outside the canonical TL;DR block
- add paragraph comments or multiline explanatory prose outside the TL;DR block
- let local comments become mini documentation essays instead of one-line intent markers
- add suppression directives like `noqa`, `type: ignore`, `@ts-ignore`, `eslint-disable`, or `biome-ignore`
- use repo-level suppression flags like `skipLibCheck` or `ignoreDeprecations`
- leave commented-out code or commented-out markup in place as fake documentation

---

## ✅ Relationship to verification

`tools/verify/headers.py` enforces the required header markers and top-of-file layout for the covered Python, TypeScript, JavaScript, YAML, TOML, shell, and dotenv families.

That verifier also covers CSS TL;DR headers with CSS-safe handling for later single-line block comments.

That verifier also rejects extra multiline comment forms outside the TL;DR block where the language supports them.

`tools/verify/suppressions.py` enforces the repo-wide ban on committed suppression directives and suppression-oriented TypeScript config flags.

`tools/verify/commentary.py` enforces local comment presence and bans commented-out code across governed comment-bearing file families.

`tools/verify/html_ship.py` enforces the ship-facing HTML rule by rejecting sensitive source comments and proving built extension HTML strips all comments.

Reviewer guidance still owns the semantic check that each later single-line comment carries one local intent.

`docs/templates/code-tldr.md` owns the reusable header skeletons.
