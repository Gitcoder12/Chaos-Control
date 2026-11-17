"""Command-line entry point for the deterministic Chaos-Control MVP."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sqlite3
import sys
import tempfile
from collections import Counter
from contextlib import suppress
from pathlib import Path
from typing import Iterable

from Collector import Collector, DirectorySource, FileSource, HTTPSource
from pipeline import CurationPipeline


def _source_for(value: str, exclude_paths: Iterable[Path] = ()):
    if value.startswith(("http://", "https://")):
        return HTTPSource(value)
    path = Path(value)
    if path.is_dir():
        return DirectorySource(path, exclude_paths=exclude_paths)
    return FileSource(path)


async def _process(sources: list[str], output: Path, max_concurrent: int) -> int:
    if isinstance(max_concurrent, bool) or max_concurrent < 1:
        raise ValueError("max_concurrent must be at least 1")
    if output.exists() and output.is_dir():
        raise IsADirectoryError(f"output path is a directory: {output}")

    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    counts: Counter[str] = Counter()
    total = 0
    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{output.name}.",
            suffix=".tmp",
            dir=output.parent,
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            collector = Collector(max_concurrent=max_concurrent)
            excluded_paths = (output, temporary_path.resolve())
            for source in sources:
                collector.add(_source_for(source, exclude_paths=excluded_paths))

            async for item in CurationPipeline().process(collector.stream()):
                handle.write(json.dumps(item, ensure_ascii=False, allow_nan=False) + "\n")
                counts[item["status"]] += 1
                total += 1

        os.replace(temporary_path, output)
        temporary_path = None
    finally:
        if temporary_path is not None:
            with suppress(OSError):
                temporary_path.unlink(missing_ok=True)

    print(f"Processed records: {total}")
    print(f"Accepted: {counts['accepted']}")
    print(f"Duplicates: {counts['duplicate']}")
    print(f"Quarantined: {counts['quarantined']}")
    print(f"JSONL output: {output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chaos-control",
        description="Stream, normalize, deduplicate, and report source records.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    process = subparsers.add_parser("process", help="Curate one or more local or HTTP sources.")
    process.add_argument("sources", nargs="+", help="Input file, directory, or HTTP(S) JSONL URL.")
    process.add_argument("--output", required=True, type=Path, help="Output JSONL path.")
    process.add_argument("--max-concurrent", type=int, default=8)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "process":
        try:
            return asyncio.run(_process(args.sources, args.output, args.max_concurrent))
        except (OSError, ValueError, TypeError, RuntimeError, sqlite3.Error) as exc:
            print(f"chaos-control: {exc}", file=sys.stderr)
            return 2
    parser.error("unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
