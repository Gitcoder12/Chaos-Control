# Project Status — Chaos-Control

**Snapshot date:** 2026-11-16  
**Status type:** Initial documentation and repository-tree assessment  
**Default branch:** main  
**Review completeness:** Partial — not a code audit or release certification

## Project purpose
Data-curation pipeline concept/codebase for ingesting, cleaning, deduplicating, classifying, extracting entities, tracking volatile fields, detecting gaps and quarantining records.

## Current maturity (README-declared or visible scaffolding; not independently verified)
Root includes Collector.py, tests/, README.md, NOTICE and .github/. README describes broad pipeline stages and scale claims; only one top-level collector and test directory were visible here, so implementation coverage needs inspection.

## Observed repository structure
Collector.py, tests/, .github/, README.md, LICENSE and NOTICE.

## Known issues and risks to investigate
README claims streaming scale from 100MB to 100TB, MinHash/LSH deduplication, entity extraction, gap detection and provenance. These claims require benchmark/evidence; examples include person/entity facts that need source attribution and should not be mistaken for verified current data. No tests or scale benchmarks run.

## Recommended next actions
Inspect Collector.py and tests to map actual supported formats/stages; build deterministic fixtures with preserved source provenance; verify exact/near-duplicate behavior and volatile TTL logic; benchmark memory/throughput on stated data volumes before any scale claim; clearly label examples as synthetic.

## Verification record
| Check | Result |
|---|---|
| Default-branch top-level tree | Inspected |
| README | Inspected |
| Deep source review | Not performed |
| Tests / build / runtime | Not run |
| Security / dependency audit | Not run |
| Live deployment / API checks | Not run |
| Independent review | Not performed |

## Change log
- 2026-11-16: Added this initial status snapshot on a review branch. No application code or existing data changed.

> Update this file only after the corresponding inspection or verification has actually been performed. Distinguish observed facts, README claims, hypotheses and unrun checks.