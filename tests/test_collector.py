"""Tests for the current Chaos-Control collector foundation."""

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from Collector import Collector, DirectorySource, FileSource


class CollectorTests(unittest.TestCase):
    def test_jsonl_file_source_normalizes_records(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.jsonl"
            path.write_text(
                json.dumps({"text": "first", "source": "unit"}) + "\n"
                + json.dumps({"content": "second", "tag": "demo"}) + "\n",
                encoding="utf-8",
            )

            async def collect():
                return [record async for record in FileSource(path).stream()]

            records = asyncio.run(collect())

            self.assertEqual([record.text for record in records], ["first", "second"])
            self.assertEqual(records[0].source, "unit")
            self.assertEqual(records[1].metadata["tag"], "demo")

    def test_csv_file_source_selects_text_column(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.csv"
            path.write_text("id,content,url\n1,alpha,https://example.com/a\n", encoding="utf-8")

            async def collect():
                return [record async for record in FileSource(path).stream()]

            records = asyncio.run(collect())

            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].text, "alpha")
            self.assertEqual(records[0].url, "https://example.com/a")
            self.assertEqual(records[0].metadata["id"], "1")

    def test_directory_source_recursively_collects_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "one.txt").write_text("first\n", encoding="utf-8")
            nested = root / "nested"
            nested.mkdir()
            (nested / "two.txt").write_text("second\n", encoding="utf-8")

            async def collect():
                return [record async for record in DirectorySource(root).stream()]

            records = asyncio.run(collect())

            self.assertEqual(sorted(record.text for record in records), ["first", "second"])

    def test_collector_merges_multiple_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.txt").write_text("alpha\n", encoding="utf-8")
            (root / "b.txt").write_text("beta\n", encoding="utf-8")

            async def collect():
                collector = Collector(max_concurrent=2)
                collector.add(FileSource(root / "a.txt"))
                collector.add(FileSource(root / "b.txt"))
                return [record async for record in collector.stream()]

            records = asyncio.run(collect())

            self.assertEqual(sorted(record.text for record in records), ["alpha", "beta"])


if __name__ == "__main__":
    unittest.main()
