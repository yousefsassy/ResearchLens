"""Small append-only feedback store with no personal data."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import threading

from app.schemas import FeedbackRequest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = PROJECT_ROOT / "data" / "feedback" / "feedback.jsonl"


class FeedbackStore:
    def __init__(self, path: Path | str | None = None):
        configured = os.environ.get("RESEARCHLENS_FEEDBACK_PATH")
        self.path = Path(path or configured or DEFAULT_PATH)
        self._lock = threading.Lock()

    def add(self, feedback: FeedbackRequest) -> None:
        record = {
            "created_utc": datetime.now(timezone.utc).isoformat(),
            **feedback.model_dump(mode="json"),
        }
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
