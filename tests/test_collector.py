"""Tests for collector parsing, directory safety, and failure propagation."""

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from Collector import CollectionError, Collector, DirectorySource, FileSource


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

    def test_directory_source_ignores_repository_and_virtualenv_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "real.txt").write_text("keep\n", encoding="utf-8")
            for name in (".git", ".venv", "node_modules", "__pycache__"):
                ignored = root / name
                ignored.mkdir()
                (ignored / "hidden.txt").write_text("ignore\n", encoding="utf-8")

            async def collect():
                return [record async for record in DirectorySource(root).stream()]

            records = asyncio.run(collect())
            self.assertEqual([record.text for record in records], ["keep"])

    def test_directory_source_excludes_output_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.txt"
            output = root / "curated.jsonl"
            temporary = root / ".curated.jsonl.tmp"
            source.write_text("source record\n", encoding="utf-8")
            output.write_text("old output\n", encoding="utf-8")
            temporary.write_text("temporary output\n", encoding="utf-8")

            async def collect():
                return [
                    record async for record in DirectorySource(
                        root, exclude_paths=[output, temporary]
                    ).stream()
                ]

            records = asyncio.run(collect())
            self.assertEqual([record.text for record in records], ["source record"])

    def test_missing_file_fails_instead_of_silently_returning_zero_records(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.jsonl"

            async def collect():
                return [record async for record in FileSource(missing).stream()]

            with self.assertRaises(FileNotFoundError):
                asyncio.run(collect())

    def test_collector_propagates_source_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            collector = Collector(max_concurrent=2)
            collector.add(FileSource(Path(directory) / "missing.txt"))

            async def collect():
                return [record async for record in collector.stream()]

            with self.assertRaises(CollectionError):
                asyncio.run(collect())

    def test_collector_validates_resource_limits(self):
        with self.assertRaises(ValueError):
            Collector(max_concurrent=0)
        with self.assertRaises(ValueError):
            Collector(queue_size=0)
        with self.assertRaises(ValueError):
            Collector(max_concurrent=True)

    def test_collector_requires_at_least_one_source(self):
        async def collect():
            return [record async for record in Collector().stream()]

        with self.assertRaises(ValueError):
            asyncio.run(collect())


if __name__ == "__main__":
    unittest.main()
