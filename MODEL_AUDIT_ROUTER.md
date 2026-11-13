# Independent Model Audit Router — Chaos-Control

**Revision date:** 2026-11-13

## Data integrity: non-negotiable
- Never replace real or maintainer-provided data with fabricated, generated, synthetic or placeholder records.
- Trace each source, licence, collection date and Git-history baseline before touching data.
- When provenance is missing, preserve the existing record and mark it unknown/unverified. Never invent a replacement.
- Synthetic fixtures may be used only in labelled tests/examples and must be isolated from runtime/production data.
- Never invent people, companies, official records, citations, metrics, benchmark results, deployments, customers or endorsements.
- Never claim a test passed unless it ran on the exact commit reviewed.

## README preservation
Recover and preserve the last maintainer-authored README from Git history. Do not rewrite or replace it. Any AI-generated notes must be dated, clearly labelled, secondary and appended at the very bottom only.

## Independent review roles
1. Data provenance checker.
2. Source/architecture/API reviewer.
3. Security/privacy/dependency reviewer.
4. Test/CI/build/reproducibility reviewer.
5. README history/licence/attribution reviewer.
6. Recruiter/research claims and public evidence reviewer.

## Audit sequence
1. Record URL, default branch, exact HEAD SHA, fork status and PR head.
2. Classify changes as merged, open, closed-unmerged, reverted or unverified.
3. Inventory runtime data, fixtures, generated files, APIs, and provenance.
4. Compare README with its pre-AI Git-history version.
5. Run documented build/lint/test commands on the exact commit; inspect CI for failure suppression.
6. Audit security, privacy, accessibility, error handling, boundaries and performance.
7. Check public claims and links. Company fit is not proof of adoption or endorsement.
8. Publish findings before editing code or data.

## Finding format
Severity (**P0/P1/P2/P3**), exact path/line, reproduction, expected vs actual, evidence and SHA, confirmed/suspected/unverifiable status, minimal fix, regression test, and impact on data/README.

## Merge gate
- [ ] No fabricated data shown as real or official.
- [ ] Real/user-provided data preserved with no silent substitutions.
- [ ] Synthetic data clearly labelled and isolated.
- [ ] Original README preserved; AI notes at bottom only.
- [ ] Tests/CI verified on exact PR head; failures disclosed.
- [ ] No secrets, private personal details, classified or confidential information.
- [ ] Attribution and licensing preserved.
- [ ] Second independent review and maintainer approval completed.

Repository: **Chaos-Control**. Do not infer features from title/roadmap. Do not merge, delete, force-push, overwrite datasets or change the original README during audit. Repository owner has final approval.
