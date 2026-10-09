# Chaos-Control

> Turn scattered data into organized knowledge. Clean, classify, detect gaps, handle volatile fields.

Chaos-Control is a data curation pipeline for LLM training, RAG systems, knowledge bases, research datasets, and any AI workflow that needs clean data.

Takes messy, multi-source, real-world data and produces records that are clean, structured, deduplicated, classified, entity-aware, gap-aware, freshness-aware, and traceable.

**From chaos to control.**

---

## Why This Exists

Every LLM is trained on cleaned data. Every RAG system needs clean chunks. Every AI company builds this internally. But nobody releases an open-source version that handles the full lifecycle: cleaning, organizing, gap detection, and volatile data tracking. Chaos-Control does all four. Streaming. Scales from 100MB to 100TB.

---

## What It Does

| Stage | Input | Output |
|-------|-------|--------|
| Ingest | JSONL, CSV, TXT, HTML | Raw records |
| Clean | Raw records | Normalized records |
| Deduplicate | Normalized | Canonical + duplicates |
| Classify | Clean | Topic + category |
| Extract Entities | Text | People, orgs, products |
| Detect Gaps | Entity records | Missing-info report |
| Handle Volatile | Time-sensitive fields | TTL + staleness |
| Validate | Records | Quality + security flags |
| Quarantine | Suspicious | Isolated for review |
| Output | All stages | JSONL + reports |

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

chaos-control process input.jsonl --output clean/
chaos-control clean input.jsonl --output clean.jsonl
chaos-control gaps clean.jsonl --output gaps.json
chaos-control watch ./incoming --output ./cleaned

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

Pre-alpha. No working code yet.

README is the map. Code is next. First milestone: v0.1 with working process command.

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
