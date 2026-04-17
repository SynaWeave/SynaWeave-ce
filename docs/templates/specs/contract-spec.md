# 🧾 Contract spec — <name>

## 🧩 Purpose

Define the cross-surface contract, why it exists, and which boundary owns it.

## 📌 Scope

- in-scope payloads or messages
- out-of-scope behavior
- affected runtimes or tools

## 👤 Boundary owner

- owning package, service, or shared module
- upstream producers
- downstream consumers

## 🔢 Versioning and compatibility

- contract version identifier or strategy
- backwards-compatibility expectations
- migration or deprecation plan when changed

## 📥 Inputs

- required fields
- optional fields
- validation rules
- source constraints

## 📤 Outputs

- response or event shape
- envelope expectations
- consumer-facing guarantees

## 📏 Invariants

- serialization rules
- security boundaries
- field stability guarantees
- forbidden provider leakage into public shape

## ⚠️ Failure modes

- validation failures
- authorization failures
- dependency failures
- retry or idempotency implications

## 👀 Observability

- required logs, traces, metrics, or evaluation labels
- identifiers needed for correlation and debugging

## ✅ Verification

- contract tests
- integration tests
- docs or schema examples that must stay aligned

## 🔙 Rollback implications

- what breaks if the contract is reverted
- what must be migrated first

## 🔗 Related files

List the code, tests, owner docs, planning packets, and ADRs affected by this contract.
