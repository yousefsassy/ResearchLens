"""Single-worker demo authentication, rate limits and durable question allowance.

No provider credentials or authorization headers are included in diagnostics.
The allowance counts admitted questions, including failures, rather than dollars.
"""
from collections import deque
import hmac
import json
import os
from pathlib import Path
import tempfile
import threading
import time

from fastapi import HTTPException


class DemoGuard:
    def __init__(self, token="", *, required=False, budget_path=None, max_questions=100,
                 ask_per_minute=5, feedback_per_minute=20, clock=time.monotonic):
        self._token = token
        self.enabled = required or bool(token)
        self.ready = not self.enabled or (len(token) >= 32 and budget_path is not None
            and all(type(n) is int and n > 0 for n in
                    (max_questions, ask_per_minute, feedback_per_minute)))
        self.path = Path(budget_path) if budget_path else None
        self.maximum = max_questions
        self.limits = {"ask": ask_per_minute, "feedback": feedback_per_minute}
        self._events = {name: deque() for name in self.limits}
        self._lock = threading.Lock()
        self.clock = clock

    @classmethod
    def from_env(cls):
        try:
            return cls(os.environ.get("RESEARCHLENS_API_TOKEN", ""),
                required=os.environ.get("RESEARCHLENS_REQUIRE_AUTH", "").lower() == "true",
                budget_path=os.environ.get("RESEARCHLENS_BUDGET_PATH", "data/demo/budget.json"),
                max_questions=int(os.environ.get("RESEARCHLENS_MAX_QUESTIONS", "100")),
                ask_per_minute=int(os.environ.get("RESEARCHLENS_ASK_PER_MINUTE", "5")),
                feedback_per_minute=int(os.environ.get("RESEARCHLENS_FEEDBACK_PER_MINUTE", "20")))
        except ValueError:
            guard = cls(required=True)
            guard.ready = False
            return guard

    def _reserve(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            state = json.loads(self.path.read_text())
            used = state["questions"]
            if state.get("version") != 1 or type(used) is not int or used < 0:
                raise ValueError("Invalid budget state")
        else:
            used = 0
        if used >= self.maximum:
            raise HTTPException(429, "The demonstration question allowance is exhausted.")
        name = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", dir=self.path.parent, delete=False) as f:
                name = f.name  # tempfile creates a mode-0600 file
                json.dump({"version": 1, "questions": used + 1}, f)
                f.flush()
                os.fsync(f.fileno())
            os.replace(name, self.path)
            directory = os.open(self.path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            if name and os.path.exists(name):
                os.unlink(name)

    def admit(self, authorization, endpoint):
        if not self.enabled:
            return
        if not self.ready:
            raise HTTPException(503, "Demo protection is not configured.")
        expected = "Bearer " + self._token
        if not hmac.compare_digest((authorization or "").encode(), expected.encode()):
            raise HTTPException(401, "API authentication required.", headers={"WWW-Authenticate": "Bearer"})
        with self._lock:
            now = self.clock()
            events = self._events[endpoint]
            while events and now - events[0] >= 60:
                events.popleft()
            if len(events) >= self.limits[endpoint]:
                raise HTTPException(429, "Demo rate limit reached. Please wait.",
                                    headers={"Retry-After": "60"})
            if endpoint == "ask":
                try:
                    self._reserve()
                except (OSError, ValueError, KeyError, TypeError):
                    raise HTTPException(503, "Demo allowance storage is unavailable.") from None
            events.append(now)
