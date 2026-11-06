import json
import pytest
from src.retrieval.common import load_chunks


def test_roundtrip_preserves_order_and_metadata(config, chunks):
    assert load_chunks(config.chunks_path) == chunks


@pytest.mark.parametrize("change", [
    {"text": " "}, {"text": None}, {"pdf_page": True}, {"pdf_page": 0},
    {"chunk_id": ""}, {"paper_id": None}, {"pdf_filename": 1},
    {"needs_review": 1}, {"review_flags": "bad"}, {"review_flags": [3]}])
def test_invalid_fields(config, chunks, change):
    chunks[0].update(change)
    config.chunks_path.write_text(json.dumps(chunks[0]), encoding="utf-8")
    with pytest.raises(ValueError, match="line 1"):
        load_chunks(config.chunks_path)


@pytest.mark.parametrize("payload", ["", "\n", "{broken", "[]", "null", "{}"])
def test_invalid_json_or_empty(config, payload):
    config.chunks_path.write_text(payload, encoding="utf-8")
    with pytest.raises(ValueError):
        load_chunks(config.chunks_path)


def test_duplicates(config, chunks):
    config.chunks_path.write_text((json.dumps(chunks[0]) + "\n") * 2, encoding="utf-8")
    with pytest.raises(ValueError, match="line 2.*duplicate"):
        load_chunks(config.chunks_path)


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_chunks(tmp_path / "absent.jsonl")
