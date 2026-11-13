# Contributing to Chaos-Control

1. Read README.md, FEATURE_UPGRADE_PLAN.md and ACTIVITY_LOG.md.
2. Pick one bounded source adapter, schema or concurrency task.
3. Create a feature branch.
4. Add fixtures and tests for valid, malformed, oversized and failing sources.
5. Test cancellation, resource cleanup and backpressure where relevant.
6. Include exact commands, Python/dependency versions and results in the PR.
7. Update ACTIVITY_LOG.md with evidence.

Do not add unbounded network fetching or unsafe filesystem traversal. Human maintainers approve merges and releases.
