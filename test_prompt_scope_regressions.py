"""Regression checks for scope-aware comparison and safe abstention instructions."""
from src.generation.papers import interpret, load_catalog
from src.generation.prompts import SYSTEM_PROMPT, build_repair_messages
from src.generation.schemas import Evidence, ModelAnswer
from pathlib import Path


def test_comparison_unit_targets_method_evidence():
    catalog = load_catalog(Path('data/papers_generation.json'))
    result = interpret('Compare the unit of evaluation in SelfCheckGPT and FActScore', None, 'auto', catalog)
    assert result.answer_type == 'comparison'
    assert result.aspects == ['methods']


def test_comparison_explicit_limitation_scope():
    catalog = load_catalog(Path('data/papers_generation.json'))
    result = interpret('Compare the methods and limitations of SelfCheckGPT and FActScore', None, 'auto', catalog)
    assert result.aspects == ['methods', 'limitations']


def test_abstention_and_quote_repair_guidance():
    assert "claims []" in SYSTEM_PROMPT
    assert "do not guess" in SYSTEM_PROMPT
