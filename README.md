# Chaos-Control

> Collect and curate data streams with traceable provenance. Current MVP: normalize text, detect exact duplicates, quarantine invalid records, and export JSONL.

Chaos-Control is a data curation pipeline for LLM training, RAG systems, knowledge bases, research datasets, and any AI workflow that needs clean data.

Current release candidate (0.2.1) provides multi-source collection plus a deterministic curation slice. It does not yet implement the full lifecycle described in the roadmap below.

**From chaos to control.**

---

## Why This Exists

AI and retrieval systems depend on trustworthy data preparation. Chaos-Control is being built as a composable, streaming-first open-source toolkit. The current release is deliberately narrower than the long-term vision: no 100TB scale claim, semantic deduplication, entity resolution, or automated freshness tracking is made.

---

## Intended lifecycle

The following is the target architecture, not a claim that every stage is implemented in v0.2.0.

| Stage | Input | Target output | Current status |
|-------|-------|--------|
| Ingest | Local JSONL/NDJSON, CSV, TXT, folders; HTTP(S) JSONL | Raw records | Implemented for the listed source types |
| Clean | Raw records | Normalized records | Basic HTML/text, Unicode and whitespace normalization implemented |
| Deduplicate | Normalized | Canonical + duplicates | Exact normalized-text deduplication implemented; semantic/MinHash planned |
| Classify | Clean | Topic + category | Planned; not implemented |
| Extract Entities | Text | People, orgs, products | Planned; not implemented |
| Detect Gaps | Entity records | Missing-info report | Basic required-field quarantine only; entity-aware gap analysis planned |
| Handle Volatile | Time-sensitive fields | TTL + staleness | Planned; not implemented |
| Validate | Records | Quality + security flags | Basic emptiness/required-field/malformed-input flags implemented |
| Quarantine | Suspicious | Isolated for review | Output status and reason flags implemented; persistent review queue planned |
| Output | All stages | JSONL + reports | JSONL output implemented; aggregate quality reports planned |

---

## The Core Pipeline

Input -> Ingest -> Clean -> Deduplicate -> Classify -> Extract Entities -> Detect Gaps -> Handle Volatile -> Validate -> Keep/Quarantine -> Output

---

## Example

Input (messy, multi-source):

{"source":"reddit","text":"<p>Sam Altman is CEO of OpenAI!! https://t.co/abc</p>"}
{"source":"wikipedia","text":"Sam Altman (born April 22, 1985) is an American entrepreneur."}
{"source":"twitter","text":"Sam Altman is CEO of OpenAI!! https://t.co/abc"}
{"source":"blog","text":"        "}
{"source":"scrape","text":"SAM ALTMAN — CEO — OPENAI — NET WORTH $2B (2023)"}

Output (clean, organized, gap-aware):

{"id":"doc_001","text":"Sam Altman is CEO of OpenAI.","topic":"ai-leadership","entities":["Sam Altman","OpenAI"],"source":"reddit","quality_score":0.72}
{"id":"doc_002","text":"Sam Altman (born April 22, 1985) is an American entrepreneur.","topic":"ai-leadership","entities":["Sam Altman"],"source":"wikipedia","quality_score":0.95}
{"id":"doc_003","duplicate_of":"doc_001","reason":"near_duplicate","dropped":true}
{"id":"doc_004","dropped":true,"reason":"empty_after_cleaning"}
{"id":"doc_005","text":"Sam Altman is CEO of OpenAI.","volatile_fields":{"net_worth":{"value":"$2B","last_updated":"2023-01-01","ttl_days":30,"stale":true}}}

Gaps report:

Entity: Sam Altman
  OK  birth_date  (wikipedia)
  OK  role        (wikipedia)
  MISSING education
  MISSING current_projects
  STALE   net_worth (>30 days old)

More examples: see docs/examples.md (60+ real-world cases).

---

## Core Concepts

Streaming — process data as it flows, never load the whole corpus.

Deduplication — exact + near-duplicate detection via MinHash/LSH.

Entity extraction — extract people, orgs, products, locations.

Topic classification — assign topic tags. v0.1 rules, v0.2 LLM.

Gap detection — for each entity, which expected fields are missing.

Volatile tracking — mark fields with TTLs (net worth, followers, prices).

Provenance — keep source, URL, retrieval time per record.

Quarantine — isolate suspicious records for review, never auto-delete.

---

## Data Quality Actions

| Condition | Action |
|-----------|--------|
| Valid | Keep |
| Exact duplicate | Drop |
| Near duplicate | Merge/quarantine |
| Empty | Drop |
| Spam | Drop/quarantine |
| Low quality | Drop/quarantine |
| Missing fields | Keep + report gap |
| Stale field | Keep + mark stale |
| Conflict | Preserve + flag |
| Malformed | Quarantine |
| Suspicious content | Quarantine |
| Prompt injection | Flag + quarantine |
| Language mismatch | Filter/quarantine |

---

## CLI

chaos-control process input.jsonl --output curated.jsonl
chaos-control process ./incoming --output curated.jsonl --max-concurrent 8

---

## Output Schema

{
  "id": "doc_001",
  "text": "Cleaned text",
  "source": "example",
  "topic": "ai-research",
  "entities": ["Example Entity"],
  "quality_score": 0.91,
  "duplicate_of": null,
  "volatile_fields": {},
  "gaps": [],
  "flags": []
}

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| Language | Python 3.11+ |
| CLI | Typer |
| Streaming | datasets, ijson |
| Dedup | datasketch (MinHash) |
| Unicode | ftfy |
| Language detection | langdetect |
| Entities | spaCy |
| Config | pydantic-settings |
| Testing | pytest |

---

## Installation

git clone https://github.com/Gitcoder12/Chaos-Control.git
cd Chaos-Control
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

---

## Roadmap

v0.1 — Core Pipeline
Streaming ingestion, HTML extraction, dedup (MinHash), normalization, rule-based classification, gap detection, CLI, tests, docs.

v0.2 — Intelligence
LLM classification (via Resonance), entity extraction (spaCy), entity resolution, knowledge graph.

v0.3 — Lifecycle
Volatile field tracking, record versioning, watch mode, provenance.

v0.4 — Scale
Parallel processing, cloud storage (S3/GCS), CommonCrawl workflows, benchmarks.

v1.0 — Production
Docker + CI, HuggingFace integration, published paper, stable API.

---

## Design Principles

1. Streaming first.
2. Honest scope.
3. Composable stages.
4. Preserve provenance.
5. Preserve conflicts.
6. Separate data from instructions.
7. Quarantine before destruction.
8. Measurable.
9. Reproducible.
10. Domain-agnostic.

---

## Status

v0.2.1 MVP (development): local/HTTP collection, deterministic text normalization, exact deduplication, required-field checks, quarantine flags, provenance-preserving JSONL output, installable CLI, explicit source-failure propagation, strict JSON constants, atomic output publication, and automated tests across supported Python versions. This is not yet a production-grade full data-curation platform.

Collection behavior: missing files, invalid directories, unavailable HTTP dependencies, and exhausted HTTP retries fail the run rather than silently producing a partial dataset. The CLI writes to a temporary file and only publishes it after every source completes; prior output remains untouched after a failure.

Not yet implemented: semantic/MinHash deduplication, topic classification, entity extraction/resolution, entity-level gap reports, TTL/freshness monitoring, persistent quarantine review, parallel distributed processing, cloud storage, Hugging Face integration, and 100TB-scale benchmarking. The next milestone is measured correctness and performance for the current pipeline before adding more stages.

---

## Related Projects

| Repo | Role |
|------|------|
| Chaos-Control | Data curation (this repo) |
| Burst | Fast C++ tokenizer |
| Resonance | LLM query router |
| Overdrive | Process analyzer |
| ARK | AI Safety Research |

Flow: Chaos-Control -> Burst -> Resonance -> Overdrive -> ARK

---

## License

Apache License 2.0.

---

## Author

Dharavath Satvik — @Gitcoder12


---

## AI-maintained project notes (secondary — 2026-11-13)

This section supplements the maintainer-authored README above. The original text has been restored verbatim from Git-history baseline `a22d862e0e36b51fe8800043fe542fc617deaf3c`; this addendum does not replace or certify original claims.

- The original README labels the project pre-alpha. Later commits add an asynchronous collector and tests; verify the currently available collector and supported inputs before claiming full lifecycle or large-scale processing.
- The source tree, runtime data and tests are the implementation source of truth. A roadmap item or draft PR is not a shipped feature by itself.
- Preserve existing real and maintainer-provided data. Never silently substitute generated or placeholder records. Mark unverified sources and metrics as unknown/unverified.
- Verify installation, execution, tests and public claims against the exact current commit before presenting this project to recruiters, researchers or professors.
- See [MODEL_AUDIT_ROUTER.md](MODEL_AUDIT_ROUTER.md) for independent model review instructions and the merge gate.

---

## Engineering Audit & Handover — 2026-11-17

**Reviewed commit:** `62e67763c4ba772f7c593b10828d8e6c46114513` (`main`). Static inspection covered `Collector.py`, `pipeline.py`, and current collector/pipeline tests; tests were not executed.

### Confirmed findings
- The current pipeline explicitly implements text normalization, exact deduplication, required-field checks, quarantine flags, and provenance-preserving output. Its module documentation explicitly excludes semantic deduplication, entity extraction, topic inference, freshness prediction, and distributed scale.
- Existing tests cover representative file collection, normalization, provenance, exact duplicates, quarantine, and disabling deduplication. They do not establish arbitrary-scale performance or production reliability.
- The collector's broad “Any size. Any location.” wording should be treated as an aspiration, not a verified capacity guarantee.

### Next actions
1. Keep implemented and planned pipeline stages clearly separated in product claims.
2. Add adversarial tests for malformed/huge records, HTTP timeouts/retries, cancellation, temporary SQLite cleanup, and disk exhaustion.
3. Benchmark throughput and memory on documented hardware/dataset sizes before publishing scale claims.

**Verification status:** static source/test inspection only; no test suite or load benchmark was run in this audit.

---

## Examples Used
- Cleaning duplicate records collected from multiple sources
- Quarantining malformed or empty documents
- Preserving source provenance when conflicting claims appear


---

## Comparison with Existing Open-Source Projects

Chaos-Control is documented as a provenance-aware data-curation pipeline for LLM/RAG datasets, with a deliberately narrow current release: ingestion, normalization, exact deduplication, validation/quarantine and JSONL output. These projects provide adjacent data-quality and deduplication references.

| Project | Established focus | Relationship to Chaos-Control |
|---|---|---|
| [Great Expectations](https://github.com/great-expectations/great_expectations) | Data validation and quality expectations across data pipelines | A broader data-quality framework; Chaos-Control's stated distinction is a composable text/record curation pipeline with explicit quarantine and source provenance. |
| [Cleanlab](https://github.com/cleanlab/cleanlab) | Finding data and label quality issues, especially in ML datasets | More focused on statistical data/label issue detection; Chaos-Control currently performs deterministic normalization and structural checks rather than learned quality estimation. |
| [datasketch](https://github.com/ekzhu/datasketch) | Probabilistic data structures including MinHash and locality-sensitive hashing | Relevant to the planned near-duplicate stage; Chaos-Control currently documents exact normalized-text deduplication, not semantic or MinHash deduplication. |

### Where Chaos-Control is different
- **Explicit quarantine workflow:** invalid or insufficiently structured records can be retained with reasons instead of silently discarded.
- **Provenance-oriented design:** source and retrieval metadata are part of the intended record lifecycle.
- **Narrow deterministic MVP:** the current implementation avoids claiming large-scale semantic classification, entity resolution or freshness automation before those stages exist.

### Where established projects are stronger
Great Expectations and Cleanlab have much broader data-quality ecosystems and integrations. datasketch provides specialized similarity primitives. Chaos-Control's README explicitly marks several stages—classification, entity extraction, semantic deduplication and volatile-field tracking—as planned or partial.

### Evidence and limitations
Measure throughput and memory on reproducible datasets; test schema drift, malformed records, Unicode normalization, duplicate edge cases and provenance preservation. Keep the current release scope distinct from the target architecture. This is a capability-scope comparison, not a scale or quality benchmark.
