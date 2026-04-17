# 🧱 Code TL;DR template

Use this file as the durable visual reference for the repo's comment-heavy style.

Durable policy lives in `docs/code-style.md`.
Hooks and verifier scripts stay strict feedback loops instead of second policy homes.

## TL;DR

Group files by comment syntax family.

Keep the marker order exact in every governed TL;DR block:

1. `TL;DR  -->`
2. `- Later Extension Points:`
3. `- Role:`
4. `- Exports:`
5. `- Consumed By:`

Keep local comments brief.
Keep them one physical line per intent.
Keep them note-taking shaped instead of prose-heavy.

## Syntax families

### Wrapped TL;DR families

- Python uses one top-of-file triple-quoted TL;DR block with `~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~` wrappers.
- TypeScript, JavaScript, and CSS use one top-of-file block-comment TL;DR block with `~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~` wrappers.
- In wrapped families, the TL;DR block is the only multiline explanation block in the file.
- CSS is the narrow exception for later syntax: local CSS comments still use `/* ... */`, but each later comment must stay one physical line per intent.

### Hash-comment TL;DR families

- YAML, workflow YAML, TOML, shell-style files, and `.env.example` use one contiguous top-of-file `#` comment block.
- Shell keeps the shebang first, then places the TL;DR block immediately after it.
- This repo preserves `~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~` separator rows in hash-comment TL;DR blocks for visual scanning consistency.
- Blank separator rows inside that block stay as bare `#` lines.

### HTML note block family

- HTML stays review-governed instead of TL;DR-enforced because literal `TL;DR  -->` markers would collide with HTML comment closing syntax.
- New HTML files should still open with a short note block after `<!DOCTYPE html>` that explains page role, key structure, and consumer path with one line per intent.

## Visual examples

### Python

```py
"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  repo verification entrypoint for script and coordination checks

- Later Extension Points:
    --> add broader repo-control checks as later quality gates become active

- Role:
    --> runs the bounded verification checks that keep repo-control changes explainable and safe

- Exports:
    --> `main()` command-line verification entrypoint

- Consumed By:
    --> reviewers integrators and local operators running repo verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

# ---------- runtime identity ----------

# Keep required TL;DR markers centralized for every script audit.
TLDR_REQUIRED_MARKERS = (
    "TL;DR  -->",
)
```

### TypeScript / JavaScript / CSS

```ts
/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  render the recipes route

- Later Extension Points:
  --> add later list filters only when the recipes contract widens

- Role:
  --> presents approved recipe reads without widening into draft editing

- Exports:
  --> `RecipesPageComponent`

- Consumed By:
  --> `apps/web/src/routes.ts`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */

// ---------- route view model ----------

// Keep route-local copy near the component that renders it.
const recipesHeading = "Approved Recipes";
```

### YAML / TOML / shell / `.env.example`

```text
#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# TL;DR  -->  API service container surface
#
# - Later Extension Points:
#   --> add narrower container hardening only when the platform proof path needs it
#
# - Role:
#   --> builds one API image surface for local and cluster runtime packaging
#
# - Exports:
#   --> one API container build recipe
#
# - Consumed By:
#   --> platform/k8s/api.yaml
#   --> local operator flows through tools/scripts/dev.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# ---------- runtime identity ----------
# Keep image metadata aligned across local and cluster packaging.
ARG SVC=api
```

### HTML

```html
<!DOCTYPE html>
<!-- page shell for the bounded recipes route -->
<!-- keep the loader script and root node obvious for reviewers -->
<html lang="en">
```

Use HTML comments only for source notes.

Do not place sensitive theory in them.

Shipped HTML artifacts must strip them.

## Usage notes

- Keep the `  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~` rows in governed TL;DR blocks.
- Keep non-TL;DR body comments one physical line per intent.
- Keep local comments specific about what the nearby group does and why the strategy stays that way.
- Treat declaration-bound Python docstrings as the only narrow carve-out to the one-line body-comment rule.
- Extend this file only when a comment-syntax family or governed example shape changes across the live repo.
