"""Deterministic, streaming-first curation primitives for Chaos-Control.

This first pipeline release intentionally implements only verifiable stages:
text normalization, exact deduplication, required-field checks, quarantine
flags, and provenance-preserving output. It does not claim semantic dedup,
entity extraction, topic inference, freshness prediction, or distributed scale.
"""

from __future__ import annotations

import hashlib
import html
import re
import sqlite3
import tempfile
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, AsyncIterator, Iterable

from Collector import Record


_BLOCK_TAGS = {
    "address", "article", "blockquote", "br", "div", "footer", "h1", "h2",
    "h3", "h4", "header", "li", "main", "ol", "p", "pre", "section", "ul",
}
_IGNORED_TAGS = {"script", "style"}
_WHITESPACE = re.compile(r"\s+")


class _VisibleTextParser(HTMLParser):
    """Extract visible text while discarding script and style contents."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _IGNORED_TAGS:
            self._ignored_depth += 1
        elif self._ignored_depth == 0 and tag in _BLOCK_TAGS:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in _IGNORED_TAGS and self._ignored_depth:
            self._ignored_depth -= 1
        elif self._ignored_depth == 0 and tag in _BLOCK_TAGS:
            self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        if self._ignored_depth == 0:
            self.parts.append(data)


def normalize_text(value: str) -> str:
    """Extract visible text and normalize Unicode and whitespace deterministically."""
    if not isinstance(value, str):
        raise TypeError("record text must be a string")

    parser = _VisibleTextParser()
    try:
        parser.feed(value)
        parser.close()
        visible = " ".join(parser.parts)
    except Exception:
        # Keep malformed markup as visible text rather than silently dropping it.
        visible = html.unescape(value)

    normalized = unicodedata.normalize("NFKC", visible)
    normalized = "".join(
        " " if unicodedata.category(char) == "Cc" and char not in "\n\t" else char
        for char in normalized
    )
    return _WHITESPACE.sub(" ", normalized).strip()


class CurationPipeline:
    """Curate an async stream without holding the full corpus in memory.

    The exact-dedup index is stored in a temporary SQLite database, so memory
    use does not grow with the number of unique records. The first observed
    normalized record is the canonical record for a duplicate group.
    """

    def __init__(
        self,
        *,
        required_fields: Iterable[str] = ("text", "source"),
        deduplicate: bool = True,
    ) -> None:
        self.required_fields = tuple(required_fields)
        if any(not isinstance(name, str) or not name.strip() for name in self.required_fields):
            raise ValueError("required_fields must contain non-empty field names")
        if not isinstance(deduplicate, bool):
            raise ValueError("deduplicate must be a boolean")
        self.deduplicate = deduplicate

    async def process(self, records: AsyncIterator[Record]) -> AsyncIterator[dict[str, Any]]:
        """Yield accepted, duplicate, and quarantined record envelopes."""
        with tempfile.TemporaryDirectory(prefix="chaos-control-") as temp_dir:
            database = Path(temp_dir) / "seen.sqlite3"
            connection = sqlite3.connect(database)
            try:
                connection.execute(
                    "CREATE TABLE seen (fingerprint TEXT PRIMARY KEY, record_id TEXT NOT NULL)"
                )

                async for record in records:
                    if not isinstance(record, Record):
                        yield {
                            "id": None,
                            "status": "quarantined",
                            "flags": ["invalid_record_type"],
                            "error": "source yielded a value that is not a Record",
                        }
                        continue

                    flags: list[str] = []
                    missing: list[str] = []

                    if isinstance(record.text, str):
                        normalized = normalize_text(record.text)
                    else:
                        normalized = ""
                        flags.append("invalid_text_type")

                    source = record.source.strip() if isinstance(record.source, str) else ""
                    if not isinstance(record.source, str):
                        flags.append("invalid_source_type")

                    if record.url is None:
                        url = None
                    elif isinstance(record.url, str):
                        url = record.url.strip() or None
                    else:
                        url = None
                        flags.append("invalid_url_type")

                    if isinstance(record.metadata, dict):
                        metadata = record.metadata
                    else:
                        metadata = {}
                        flags.append("invalid_metadata_type")

                    if isinstance(record.raw, dict):
                        raw = record.raw
                    else:
                        raw = {}
                        flags.append("invalid_raw_type")

                    identity_material = "\0".join((source, url or "", normalized))
                    record_id = hashlib.sha256(identity_material.encode("utf-8")).hexdigest()

                    values: dict[str, Any] = {
                        "text": normalized,
                        "source": source,
                        "url": url,
                        **metadata,
                    }
                    for field_name in self.required_fields:
                        value = values.get(field_name)
                        if value is None or (isinstance(value, str) and not value.strip()):
                            missing.append(field_name)

                    if not normalized:
                        flags.append("empty_after_cleaning")
                    if missing:
                        flags.append("missing_required_fields")
                    if metadata.get("error") == "malformed_json":
                        flags.append("malformed_json")
                    if metadata.get("error") == "invalid_text_type":
                        flags.append("invalid_text_type")

                    status = "accepted"
                    duplicate_of: str | None = None
                    quarantine_flags = {
                        "empty_after_cleaning",
                        "invalid_text_type",
                        "invalid_source_type",
                        "invalid_url_type",
                        "invalid_metadata_type",
                        "invalid_raw_type",
                        "malformed_json",
                    }
                    if not normalized or missing or quarantine_flags.intersection(flags):
                        status = "quarantined"
                    elif self.deduplicate:
                        fingerprint = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
                        found = connection.execute(
                            "SELECT record_id FROM seen WHERE fingerprint = ?",
                            (fingerprint,),
                        ).fetchone()
                        if found:
                            status = "duplicate"
                            duplicate_of = str(found[0])
                            flags.append("exact_duplicate")
                        else:
                            connection.execute(
                                "INSERT INTO seen (fingerprint, record_id) VALUES (?, ?)",
                                (fingerprint, record_id),
                            )

                    envelope: dict[str, Any] = {
                        "id": record_id,
                        "text": normalized,
                        "source": source,
                        "url": url,
                        "metadata": metadata,
                        "raw": raw,
                        "status": status,
                        "duplicate_of": duplicate_of,
                        "flags": flags,
                    }
                    if missing:
                        envelope["missing_fields"] = missing
                    yield envelope
            finally:
                connection.close()
