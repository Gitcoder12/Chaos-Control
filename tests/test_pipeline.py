"""Unit tests for Chaos-Control's deterministic streaming curation pipeline."""

import asyncio

from Collector import Record
from pipeline import CurationPipeline, normalize_text


async def collect(items):
    async def source():
        for item in items:
            yield item

    return [item async for item in CurationPipeline().process(source())]


def test_normalize_text_extracts_visible_html_and_normalizes_unicode():
    assert normalize_text("<p>  Hello&nbsp;  world </p><script>secret()</script>") == "Hello world"


def test_pipeline_preserves_provenance_and_raw_source_payload():
    raw = {"content": "<p>Trusted source text</p>", "author": "source-author"}
    output = asyncio.run(
        collect([Record(text=raw["content"], source="unit-test", url="https://example.test/a", raw=raw)])
    )

    assert output[0]["status"] == "accepted"
    assert output[0]["text"] == "Trusted source text"
    assert output[0]["source"] == "unit-test"
    assert output[0]["url"] == "https://example.test/a"
    assert output[0]["raw"] == raw
    assert output[0]["metadata"] == {}


def test_pipeline_marks_exact_duplicates_without_discarding_them():
    items = [
        Record(text="A   useful\nrecord", source="first"),
        Record(text="<p>A useful record</p>", source="second"),
    ]
    output = asyncio.run(collect(items))

    assert [item["status"] for item in output] == ["accepted", "duplicate"]
    assert output[1]["duplicate_of"] == output[0]["id"]
    assert "exact_duplicate" in output[1]["flags"]


def test_pipeline_quarantines_empty_and_malformed_records():
    items = [
        Record(text="<script>not visible</script>", source="feed"),
        Record(text="", source="feed", metadata={"error": "malformed_json"}),
    ]
    output = asyncio.run(collect(items))

    assert all(item["status"] == "quarantined" for item in output)
    assert "empty_after_cleaning" in output[0]["flags"]
    assert "malformed_json" in output[1]["flags"]


def test_pipeline_quarantines_missing_required_source():
    item = Record(text="Some content", source="")
    output = asyncio.run(collect([item]))

    assert output[0]["status"] == "quarantined"
    assert output[0]["missing_fields"] == ["source"]


def test_pipeline_can_disable_deduplication():
    async def source():
        yield Record(text="same text", source="a")
        yield Record(text="same text", source="b")

    async def run():
        pipeline = CurationPipeline(deduplicate=False)
        return [item async for item in pipeline.process(source())]

    output = asyncio.run(run())
    assert [item["status"] for item in output] == ["accepted", "accepted"]


def test_pipeline_quarantines_non_string_text_and_malformed_metadata():
    output = asyncio.run(
        collect(
            [
                Record(text=123, source="source"),
                Record(text="valid text", source="source", metadata=None),
            ]
        )
    )

    assert output[0]["status"] == "quarantined"
    assert "invalid_text_type" in output[0]["flags"]
    assert output[1]["status"] == "quarantined"
    assert "invalid_metadata_type" in output[1]["flags"]


def test_pipeline_rejects_non_boolean_deduplication_setting():
    import pytest

    with pytest.raises(ValueError, match="deduplicate"):
        CurationPipeline(deduplicate=1)
