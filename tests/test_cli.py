"""CLI integration tests for safe, atomic curation runs."""

import json

from chaos_control import main


def test_process_command_writes_jsonl_and_reports_counts(tmp_path, capsys):
    source = tmp_path / "input.jsonl"
    source.write_text(
        json.dumps({"text": "<p>Alpha record</p>", "source": "test"}) + "\n"
        + json.dumps({"text": "Alpha   record", "source": "second"}) + "\n"
        + json.dumps({"text": "   ", "source": "test"}) + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "out" / "curated.jsonl"

    exit_code = main(["process", str(source), "--output", str(output)])

    assert exit_code == 0
    records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert [record["status"] for record in records] == [
        "accepted",
        "duplicate",
        "quarantined",
    ]
    report = capsys.readouterr().out
    assert "Processed records: 3" in report
    assert "Duplicates: 1" in report
    assert "Quarantined: 1" in report


def test_process_command_rejects_invalid_concurrency(tmp_path, capsys):
    source = tmp_path / "input.txt"
    source.write_text("record\n", encoding="utf-8")

    exit_code = main(
        ["process", str(source), "--output", str(tmp_path / "out.jsonl"), "--max-concurrent", "0"]
    )

    assert exit_code == 2
    assert "max_concurrent" in capsys.readouterr().err


def test_failed_source_does_not_overwrite_previous_output(tmp_path, capsys):
    output = tmp_path / "curated.jsonl"
    output.write_text("previous valid output\n", encoding="utf-8")
    missing_source = tmp_path / "missing.jsonl"

    exit_code = main(["process", str(missing_source), "--output", str(output)])

    assert exit_code == 2
    assert output.read_text(encoding="utf-8") == "previous valid output\n"
    assert not list(tmp_path.glob(".curated.jsonl.*.tmp"))
    assert "failed" in capsys.readouterr().err.lower()


def test_directory_input_does_not_ingest_its_own_output(tmp_path):
    source = tmp_path / "source.txt"
    output = tmp_path / "curated.jsonl"
    source.write_text("one input record\n", encoding="utf-8")

    for _ in range(2):
        exit_code = main(["process", str(tmp_path), "--output", str(output)])
        assert exit_code == 0
        records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
        assert len(records) == 1
        assert records[0]["text"] == "one input record"


def test_non_finite_json_values_are_quarantined_not_written(tmp_path):
    source = tmp_path / "input.jsonl"
    source.write_text(
        '{"text":"price record","source":"test","price":NaN}\n',
        encoding="utf-8",
    )
    output = tmp_path / "curated.jsonl"

    exit_code = main(["process", str(source), "--output", str(output)])

    assert exit_code == 0
    record = json.loads(output.read_text(encoding="utf-8"))
    assert record["status"] == "quarantined"
    assert "malformed_json" in record["flags"]


def test_non_string_record_text_is_quarantined(tmp_path):
    source = tmp_path / "input.jsonl"
    source.write_text(
        json.dumps({"text": {"not": "text"}, "source": "test"}) + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "curated.jsonl"

    exit_code = main(["process", str(source), "--output", str(output)])

    assert exit_code == 0
    record = json.loads(output.read_text(encoding="utf-8"))
    assert record["status"] == "quarantined"
    assert "invalid_text_type" in record["flags"]
