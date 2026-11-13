# Chaos-Control

**An asynchronous, multi-source collector for streaming text records into a common shape.**

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)

Chaos-Control currently provides a single-file Python collector for reading local files, recursively walking directories, and optionally streaming line-oriented HTTP(S) responses. Records from each source are yielded through one asynchronous interface.

## Current Features

- Read JSONL / NDJSON, CSV, and plain-text files one record at a time.
- Recursively collect files from a directory.
- Optionally read line-oriented HTTP(S) responses through `httpx`.
- Normalize inputs into a `Record` object with text, source, URL, metadata, and raw fields.
- Run multiple sources concurrently with a bounded queue and semaphore.
- Isolate source errors so one failed source does not automatically stop the others.

## Requirements

- Python 3.10+
- Standard library for local files and directories.
- Optional `httpx` package for HTTPSource.

Install the optional HTTP dependency when needed:

```bash
python -m pip install httpx
```

## Quick Start

Clone the repository and pass one or more input files, directories, or HTTP(S) line feeds:

```bash
git clone https://github.com/Gitcoder12/Chaos-Control.git
cd Chaos-Control

python Collector.py ./data.jsonl
python Collector.py ./incoming/
python Collector.py ./data.jsonl ./incoming/ https://example.com/feed.jsonl
```

For HTTP inputs, install `httpx` first.

## Use as a Python Module

The current implementation is a top-level module file, not an installed `chaos_control` package:

```python
import asyncio
from Collector import Collector, DirectorySource, FileSource, HTTPSource

async def main():
    collector = Collector(max_concurrent=8)
    collector.add(FileSource("data/records.jsonl"))
    collector.add(DirectorySource("incoming/"))
    collector.add(HTTPSource("https://example.com/feed.jsonl"))

    async for record in collector.stream():
        print(record.source, record.text[:80])

asyncio.run(main())
```

Remove the `HTTPSource` registration when `httpx` is not installed.

## Input Handling

| Source | Behavior |
|---|---|
| JSONL / NDJSON file | Parses each non-empty line as JSON and normalizes it |
| CSV file | Reads rows incrementally; selects a common text column when available |
| TXT file | Emits one non-empty line per record |
| Directory | Recursively streams files through the local file handlers |
| HTTP(S) | Streams response lines; JSON lines are normalized, non-JSON lines are emitted as text |

## Record Shape

Each yielded record exposes:

- `text` — normalized text content
- `source` — source identifier
- `url` — source URL when available
- `metadata` — remaining structured fields
- `raw` — original record payload

## Project Structure

```text
Chaos-Control/
├── Collector.py # Collector, source adapters, record model, and CLI
├── tests/
│   └── test_collector.py
├── LICENSE
├── NOTICE
└── README.md
```

## Run Tests

```bash
python -m unittest discover -s tests -v
```

## Scope and Limitations

The committed implementation is a collector foundation. It does **not** yet implement the broader roadmap previously described for deduplication, topic classification, entity extraction, quality scoring, gap detection, volatile-field tracking, or quarantine. Those capabilities should not be treated as available features until corresponding code and tests are committed.

The HTTP adapter expects line-oriented responses. It is not a general-purpose HTML crawler or full CSV streaming parser for remote URLs. The current CLI prints records to the terminal; it does not yet write a curated output dataset or reports.

## License

Apache-2.0. See [LICENSE](LICENSE).

---

## Project handbook

- [Activity log](ACTIVITY_LOG.md) · [Feature upgrade plan](FEATURE_UPGRADE_PLAN.md)
- [Company and team fit](COMPANY_FIT.md) · [README explanation draft](README_ADDENDUM_DRAFT.md)
- [README quality checklist](README_QUALITY_CHECKLIST.md)
- [Contributing](CONTRIBUTING.md) · [Agent instructions](AGENTS.md) · [Agent skills](SKILLS.md)

## Understanding the project

### In plain language

A Python tool that reads records from several sources, converts them into one common format and lets multiple sources be read concurrently.

### Technical and research view

Single-file asynchronous Python collector that reads JSONL/NDJSON, CSV and plain text, recursively walks directories, and optionally streams line-oriented HTTP(S) responses using httpx. A bounded queue/semaphore provides concurrency and source errors can be isolated. It is a collector library/prototype, not a complete production data platform.

Document source adapters, async generator flow, queue/semaphore limits, error policy, Record fields, HTTP line handling and resource cleanup.

For future work, see [FEATURE_UPGRADE_PLAN.md](FEATURE_UPGRADE_PLAN.md), [ACTIVITY_LOG.md](ACTIVITY_LOG.md), [COMPANY_FIT.md](COMPANY_FIT.md) and [CONTRIBUTING.md](CONTRIBUTING.md).
