# Agent Instructions — Chaos-Control

Read README.md, CONTRIBUTING.md and FEATURE_UPGRADE_PLAN.md before editing.

- Inspect source adapter and async cancellation behavior before changes.
- Bound input size, network timeouts and concurrency.
- Validate URL schemes and prevent unsafe filesystem traversal.
- Add tests for malformed records, cancellation and one-source failure.
- Preserve record provenance and avoid silently dropping errors.
- Report exact benchmark method; never invent performance numbers.
- Work on a branch and submit a PR; do not merge/deploy autonomously.
