"""CLI integration tests for the first end-to-end curation workflow."""

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
