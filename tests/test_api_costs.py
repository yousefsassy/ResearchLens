import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from eval.api_costs import CostBudgetExceeded, UsageLedger, estimate_cost


def raw(cached=20):
    return SimpleNamespace(status="completed", id="response-fixture", model="gpt-5.4-nano",
        usage=SimpleNamespace(input_tokens=100, output_tokens=10,
                              input_tokens_details=SimpleNamespace(cached_tokens=cached)))


def test_cached_tokens_are_part_of_input_not_added_again():
    assert estimate_cost("gpt-5.4-nano", 100, 10, 20) == pytest.approx((80*.2+20*.02+10*1.25)/1e6)


@pytest.mark.parametrize("values", [(None,10,0),(100,None,0),(100,10,None),(100,10,101),(-1,10,0)])
def test_missing_or_invalid_usage_is_not_fabricated(values):
    assert estimate_cost("gpt-5.4-nano", *values) is None


def test_ledger_preserves_result_separates_categories_and_restores_sdk(tmp_path):
    sdk = Mock()
    sdk.responses.create.return_value = raw()
    original = sdk.responses.create
    ledger = UsageLedger(tmp_path / "usage.jsonl")
    for category in ("generation", "generation_repair", "judge"):
        with ledger.track(sdk, category):
            assert sdk.responses.create(model="gpt-5.4-nano", max_output_tokens=50) is original.return_value
    assert sdk.responses.create is original
    assert len(ledger.requests()) == 3
    expected = 3*estimate_cost("gpt-5.4-nano",100,10,20)
    assert ledger.reserved_usd == pytest.approx(expected)  # Reservations not double counted.
    restored = UsageLedger(ledger.path)
    summary = restored.summary(2,1)
    assert summary["total_estimated_usd"] == pytest.approx(expected)
    assert summary["categories"]["generation_repair"]["cached_input_tokens"] == 20
    assert summary["categories"]["generation"]["models"] == ["gpt-5.4-nano"]
    assert summary["categories"]["judge"]["question_denominator"] == 1
    assert summary["production_projection_usd"]["100"] == pytest.approx(summary["generation_per_question_usd"]*100)
    assert "no production judging" in summary["projection_assumption"]


def test_budget_stops_before_sdk_call(tmp_path):
    sdk = Mock()
    ledger = UsageLedger(tmp_path / "usage.jsonl", budget_usd=.000001)
    with ledger.track(sdk,"judge"), pytest.raises(CostBudgetExceeded):
        sdk.responses.create(model="gpt-5.4-mini",max_output_tokens=6000)
    sdk.responses.create.assert_not_called()
    assert ledger.stopped and not ledger.requests()


def test_failed_request_keeps_unknown_accounting_and_no_raw_exception(tmp_path):
    sdk = Mock()
    sdk.responses.create.side_effect = RuntimeError("private-provider-details")
    ledger = UsageLedger(tmp_path / "usage.jsonl")
    with ledger.track(sdk,"judge"), pytest.raises(RuntimeError):
        sdk.responses.create(model="gpt-5.4-mini",max_output_tokens=6000)
    summary = ledger.summary(1,0)
    assert summary["total_estimated_usd"] is None
    assert ledger.reserved_usd > 0
    assert len(ledger.requests()) == 1
    assert "private" not in ledger.path.read_text()


def test_missing_cached_usage_does_not_become_zero(tmp_path):
    sdk = Mock()
    sdk.responses.create.return_value = raw(cached=None)
    ledger = UsageLedger(tmp_path / "usage.jsonl")
    with ledger.track(sdk,"generation"):
        sdk.responses.create(model="gpt-5.4-nano",max_output_tokens=20)
    summary = ledger.summary(1,0)
    assert summary["total_estimated_usd"] is None
    assert summary["categories"]["generation"]["cached_input_tokens"] is None


def test_interrupted_reservation_is_preserved_on_reload(tmp_path):
    sdk = Mock()
    sdk.responses.create.side_effect = KeyboardInterrupt()
    ledger = UsageLedger(tmp_path / "usage.jsonl")
    with ledger.track(sdk,"generation"), pytest.raises(KeyboardInterrupt):
        sdk.responses.create(model="gpt-5.4-nano",max_output_tokens=20)
    loaded = UsageLedger(ledger.path)
    assert loaded.summary(1,0)["total_estimated_usd"] is None
    assert len(loaded.requests()) == 1


def test_report_includes_separate_verified_usage_costs(tmp_path):
    from eval.benchmark import run, read_rows
    from eval.benchmark_data import load_benchmark
    from eval.full_benchmark import build_sections
    summary = run(load_benchmark()[:1], tmp_path / "run", mode="mock")
    sdk = Mock()
    sdk.responses.create.return_value = raw()
    ledger = UsageLedger(tmp_path / "usage.jsonl")
    with ledger.track(sdk,"generation"):
        sdk.responses.create(model="gpt-5.4-nano",max_output_tokens=50)
    summary["api_usage_costs"] = ledger.summary(1,0)
    text, _ = build_sections(summary,read_rows(tmp_path / "run"))
    assert "Recorded API usage and estimated cost" in text
    assert "gpt-5.4-nano" in text
    assert "including judging" in text
    assert "not an account billing statement" in text
