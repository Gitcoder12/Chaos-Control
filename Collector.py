"""
Chaos-Control — Multi-source collector.

Collects from files, directories, HTTP(S) URLs, and streams — concurrently.
Any size. Any location. Never loads everything into memory.

Usage:
    import asyncio
    from chaos_control.collector import Collector, FileSource, HTTPSource

    async def main():
        collector = Collector(max_concurrent=10)
        collector.add(FileSource("data/big.jsonl"))
        collector.add(HTTPSource("https://example.com/feed.jsonl"))
        collector.add(FileSource("data/another.csv"))

        async for record in collector.stream():
            print(record.source, record.text[:60])

    asyncio.run(main())
"""

from __future__ import annotations

import asyncio
import csv
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator, Iterable

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 64 * 1024  # 64 KB
DEFAULT_MAX_CONCURRENT = 8
DEFAULT_RETRIES = 3


# ---------------------------------------------------------------------------
# Record — unified output across every source
# ---------------------------------------------------------------------------

@dataclass
class Record:
    """One collected record. Same shape regardless of source."""

    text: str
    source: str
    url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "source": self.source,
            "url": self.url,
            **self.metadata,
        }


# ---------------------------------------------------------------------------
# Source interface
# ---------------------------------------------------------------------------

class DataSource(ABC):
    """Base class for every source type."""

    name: str = "unknown"

    @abstractmethod
    async def stream(self) -> AsyncIterator[Record]:
        """Yield records from this source."""
        ...


# ---------------------------------------------------------------------------
# File source — streams one file (JSONL / CSV / TXT)
# ---------------------------------------------------------------------------

class FileSource(DataSource):
    """Stream a single local file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.name = f"file:{self.path.name}"

    async def stream(self) -> AsyncIterator[Record]:
        if not self.path.exists():
            logger.error("File not found: %s", self.path)
            return

        ext = self.path.suffix.lower()
        handler = {
            ".jsonl": self._jsonl,
            ".ndjson": self._jsonl,
            ".csv": self._csv,
            ".txt": self._txt,
            ".text": self._txt,
        }.get(ext, self._txt)

        async for record in handler():
            yield record

    async def _jsonl(self) -> AsyncIterator[Record]:
        async for line in _aiter_lines(self.path):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                logger.warning("Malformed JSON in %s: %s", self.name, e)
                yield Record(text="", source=self.name, metadata={"error": "malformed_json"})
                continue

            yield _record_from_dict(obj, source=self.name)

    async def _csv(self) -> AsyncIterator[Record]:
        with self.path.open("r", encoding="utf-8", errors="replace", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return
            text_col = next(
                (c for c in reader.fieldnames if c and c.lower() in ("text", "content", "body", "document")),
                reader.fieldnames[0],
            )
            for row in reader:
                yield Record(
                    text=str(row.get(text_col, "") or ""),
                    source=self.name,
                    url=row.get("url") or None,
                    metadata={k: v for k, v in row.items() if k != text_col},
                    raw=dict(row),
                )

    async def _txt(self) -> AsyncIterator[Record]:
        async for line in _aiter_lines(self.path):
            line = line.strip()
            if line:
                yield Record(text=line, source=self.name)


# ---------------------------------------------------------------------------
# Directory source — walks a folder, streams every file
# ---------------------------------------------------------------------------

class DirectorySource(DataSource):
    """Recursively collect all files in a directory."""

    def __init__(
        self,
        path: str | Path,
        pattern: str = "*",
        recursive: bool = True,
    ) -> None:
        self.path = Path(path)
        self.pattern = pattern
        self.recursive = recursive
        self.name = f"dir:{self.path.name}"

    async def stream(self) -> AsyncIterator[Record]:
        if not self.path.exists():
            logger.error("Directory not found: %s", self.path)
            return

        globber = self.path.rglob if self.recursive else self.path.glob
        for file_path in globber(self.pattern):
            if not file_path.is_file():
                continue
            async for record in FileSource(file_path).stream():
                yield record


# ---------------------------------------------------------------------------
# HTTP source — streams remote JSONL / CSV / TXT over HTTP(S)
# ---------------------------------------------------------------------------

class HTTPSource(DataSource):
    """Stream a remote URL without downloading the whole file first."""

    def __init__(
        self,
        url: str,
        retries: int = DEFAULT_RETRIES,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> None:
        self.url = url
        self.retries = retries
        self.chunk_size = chunk_size
        self.name = f"http:{url.split('/')[-1] or url}"

    async def stream(self) -> AsyncIterator[Record]:
        try:
            import httpx
        except ImportError:
            logger.error("httpx required for HTTPSource. Install: pip install httpx")
            return

        for attempt in range(1, self.retries + 1):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    async with client.stream("GET", self.url) as response:
                        response.raise_for_status()
                        async for line in _aiter_http_lines(response, self.chunk_size):
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                obj = json.loads(line)
                            except json.JSONDecodeError:
                                yield Record(text=line, source=self.name, url=self.url)
                                continue
                            record = _record_from_dict(obj, source=self.name)
                            record.url = record.url or self.url
                            yield record
                return
            except Exception as e:
                logger.warning("HTTP fetch failed (%d/%d): %s", attempt, self.retries, e)
                if attempt == self.retries:
                    logger.error("Giving up on %s", self.url)
                    return
                await asyncio.sleep(2 ** attempt)


# ---------------------------------------------------------------------------
# Collector — orchestrates all sources concurrently
# ---------------------------------------------------------------------------

class Collector:
    """Stream records from multiple sources at the same time."""

    def __init__(
        self,
        max_concurrent: int = DEFAULT_MAX_CONCURRENT,
        queue_size: int = 1000,
    ) -> None:
        self.sources: list[DataSource] = []
        self.max_concurrent = max_concurrent
        self.queue_size = queue_size

    def add(self, source: DataSource) -> "Collector":
        """Register a source. Chainable."""
        self.sources.append(source)
        return self

    def add_many(self, sources: Iterable[DataSource]) -> "Collector":
        self.sources.extend(sources)
        return self

    async def stream(self) -> AsyncIterator[Record]:
        """
        Stream records from all sources concurrently.

        Backpressure: if consumers are slow, producers pause.
        Error isolation: one source failing does not stop others.
        """
        queue: asyncio.Queue[Record | None] = asyncio.Queue(maxsize=self.queue_size)
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def produce(source: DataSource) -> None:
            async with semaphore:
                try:
                    async for record in source.stream():
                        await queue.put(record)
                except Exception as e:
                    logger.exception("Source %s failed: %s", source.name, e)
                finally:
                    await queue.put(None)  # signal done

        # Start all producers
        tasks = [asyncio.create_task(produce(s)) for s in self.sources]
        finished = 0

        try:
            while finished < len(tasks):
                item = await queue.get()
                if item is None:
                    finished += 1
                    continue
                yield item
        finally:
            for t in tasks:
                if not t.done():
                    t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _aiter_lines(path: Path, chunk_size: int = DEFAULT_CHUNK_SIZE) -> AsyncIterator[str]:
    """Async line iterator over a local file — streams in chunks."""
    loop = asyncio.get_running_loop()
    buffer = ""
    with path.open("r", encoding="utf-8", errors="replace") as f:
        while True:
            chunk = await loop.run_in_executor(None, f.read, chunk_size)
            if not chunk:
                break
            buffer += chunk
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                yield line
    if buffer:
        yield buffer


async def _aiter_http_lines(response: Any, chunk_size: int) -> AsyncIterator[str]:
    """Async line iterator over an httpx streaming response."""
    buffer = b""
    async for chunk in response.aiter_bytes(chunk_size=chunk_size):
        buffer += chunk
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            yield line.decode("utf-8", errors="replace")
    if buffer:
        yield buffer.decode("utf-8", errors="replace")


def _record_from_dict(obj: Any, source: str) -> Record:
    """Convert a raw dict (or scalar) into a Record."""
    if not isinstance(obj, dict):
        return Record(text=str(obj), source=source, raw={"value": obj})

    text = (
        obj.get("text")
        or obj.get("content")
        or obj.get("body")
        or obj.get("document")
        or ""
    )
    url = obj.get("url")
    known = {"text", "content", "body", "document", "source", "url"}
    metadata = {k: v for k, v in obj.items() if k not in known}

    return Record(
        text=str(text),
        source=str(obj.get("source", source)),
        url=str(url) if url else None,
        metadata=metadata,
        raw=obj,
    )


# ---------------------------------------------------------------------------
# CLI — run it standalone
# ---------------------------------------------------------------------------

def _main() -> None:
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m chaos_control.collector <file-or-url> [more...]")
        sys.exit(1)

    logging.basicConfig(level=logging.INFO)

    async def run() -> None:
        collector = Collector(max_concurrent=8)
        for arg in sys.argv[1:]:
            if arg.startswith(("http://", "https://")):
                collector.add(HTTPSource(arg))
            elif Path(arg).is_dir():
                collector.add(DirectorySource(arg))
            else:
                collector.add(FileSource(arg))

        n = 0
        async for record in collector.stream():
            n += 1
            print(f"[{n}] {record.source}: {record.text[:80]}")

        print(f"\nTotal: {n} records")

    asyncio.run(run())


if __name__ == "__main__":
    _main()
