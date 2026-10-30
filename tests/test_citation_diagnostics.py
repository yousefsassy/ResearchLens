import json

import pytest

from src.generation import GenerationConfig, ResearchGenerator
from src.generation.client import GenerationFailure
from test_generation import Client, Retriever, passage
from test_generation_repair import SequenceClient, invalid


def diagnostics(capsys):
    captured = capsys.readouterr()
    assert not captured.out
    return [json.loads(line.removeprefix("[citation-debug] "))
            for line in captured.err.splitlines()]


@pytest.mark.parametrize("enabled", [False, True])
def test_diagnostics_are_opt_in_and_report_successful_repair(enabled, capsys, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "credential-must-not-appear")
    client = SequenceClient([invalid("quote"), Client().result])
    result = ResearchGenerator(Retriever([passage()]), client,
        GenerationConfig(debug_citations=enabled)).answer("SelfCheckGPT")
    assert result.status == "complete" and result.metrics.attempts == 2
    events = diagnostics(capsys)
    if not enabled:
        assert events == []
        return
    error = json.loads(client.messages[1][1]["content"])["validation_error"]
    assert events[0] == {
        "attempt": "initial generation", "validation": "failed",
        "validation_error": error, "claim_index": 1, "source_id": "S1",
        "repair_attempted": False, "repair_validation": "pending",
    }
    assert events[-1] == {"repair_attempted": True, "repair_validation": "passed"}
    logged = json.dumps(events)
    assert "credential-must-not-appear" not in logged
    assert passage()["text"] not in logged
    assert client.messages[0][0]["content"] not in logged


@pytest.mark.parametrize("kind,source_id", [("source", "S999"), ("comparison", None)])
def test_both_failed_attempts_are_identified(kind, source_id, capsys):
    client = SequenceClient([invalid(kind), invalid(kind)])
    result = ResearchGenerator(Retriever([passage()]), client,
        GenerationConfig(debug_citations=True)).answer("Compare P002 and P003")
    assert result.status == "error" and len(client.messages) == 2
    events = diagnostics(capsys)
    assert [event["attempt"] for event in events[:2]] == ["initial generation", "citation-repair"]
    assert all(event["claim_index"] == 1 and event["source_id"] == source_id for event in events[:2])
    assert events[0]["validation_error"] == events[1]["validation_error"]
    assert events[-1] == {"repair_attempted": True, "repair_validation": "failed"}


@pytest.mark.parametrize("repair", [{}, GenerationFailure("openai_api_error", "private provider details")])
def test_unvalidated_repair_is_not_reported_as_citation_failure(repair, capsys):
    client = SequenceClient([invalid("quote"), repair])
    result = ResearchGenerator(Retriever([passage()]), client,
        GenerationConfig(debug_citations=True)).answer("SelfCheckGPT")
    assert result.status == "error"
    events = diagnostics(capsys)
    assert len(events) == 2
    assert events[-1] == {"repair_attempted": True, "repair_validation": "not_run"}
    assert "private provider details" not in json.dumps(events)


def test_valid_initial_answer_is_quiet(capsys):
    result = ResearchGenerator(Retriever([passage()]), Client(),
        GenerationConfig(debug_citations=True)).answer("SelfCheckGPT")
    assert result.status == "complete"
    assert diagnostics(capsys) == []


@pytest.mark.parametrize("value,expected", [("1", True), ("TRUE", True), ("on", True),
                                           ("0", False), ("false", False), ("", False)])
def test_debug_environment_switch(value, expected, tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("RESEARCHLENS_DEBUG_CITATIONS=1\n")
    monkeypatch.setenv("RESEARCHLENS_DEBUG_CITATIONS", value)
    assert GenerationConfig.from_env(env_file).debug_citations is expected
    assert GenerationConfig().debug_citations is False
