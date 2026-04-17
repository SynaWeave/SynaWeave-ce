# ✅ Verification plan — <name>

## 🧩 Objective

State what this verification packet proves and which repo or runtime claim it validates.

## 📌 Scope

- systems, docs, or workflows under test
- excluded surfaces
- failure risks being covered

## 🧱 Preconditions

- required branch state
- required fixtures, env setup, or sample data
- required dependent services or mocks

## 🧪 Execution steps

List the commands or ordered manual actions exactly.

## 📎 Evidence outputs

- logs
- screenshots
- traces or metrics
- generated artifacts

## 🎯 Expected results

- pass conditions
- required invariants
- acceptable tolerances when timing or metrics matter

## ❌ Failure interpretation

- what each failure class implies
- which owner should triage the failure
- which failures block merge or release

## 🔁 Regression check

- previous baseline compared against
- threshold that counts as regression
- rollback or follow-up action when regression appears

## 👤 Ownership

- executing owner
- reviewing owner
- downstream lane or deliverable affected by failure

## 🔗 Related files

List the tests, verifier code, workflows, owner docs, and planning packets this verification plan covers.
