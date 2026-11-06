"""Opt-in SDK usage ledger and standard text-token price estimates.

No prompts, answers, headers, credentials, or raw exceptions are persisted.
Prices verified against the official model pages on 2026-11-02.
"""
from contextlib import contextmanager
import json
import math
import os
from pathlib import Path
import time

PRICING = {
    "gpt-5.4-nano": {"input": .20, "cached_input": .02, "output": 1.25},
    "gpt-5.4-mini": {"input": .75, "cached_input": .075, "output": 4.50},
}
PRICE_SOURCES = {model: "https://developers.openai.com/api/docs/models/" + model for model in PRICING}


class CostBudgetExceeded(RuntimeError):
    pass


def estimate_cost(model, input_tokens, output_tokens, cached_input_tokens):
    """Return null for missing/invalid usage rather than inventing zeroes."""
    values = (input_tokens, output_tokens, cached_input_tokens)
    if model not in PRICING or any(type(v) is not int or v < 0 for v in values):
        return None
    if cached_input_tokens > input_tokens:
        return None
    rates = PRICING[model]
    return ((input_tokens - cached_input_tokens) * rates["input"]
            + cached_input_tokens * rates["cached_input"] + output_tokens * rates["output"]) / 1e6


class UsageLedger:
    def __init__(self, path, budget_usd=18.0):
        if not math.isfinite(budget_usd) or budget_usd <= 0:
            raise ValueError("Budget must be positive and finite")
        self.path = Path(path)
        self.budget_usd = budget_usd
        self.rows = [json.loads(line) for line in self.path.read_text().splitlines() if line.strip()] if self.path.exists() else []
        self.stopped = False

    @property
    def reserved_usd(self):
        # Failed/unknown accounting conservatively consumes the preflight reserve.
        return sum(row["estimated_usd"] if row.get("estimated_usd") is not None
                   else row["preflight_reserve_usd"] for row in self.requests())

    def _save(self, row):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as stream:
            stream.write(json.dumps(row, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        self.rows.append(row)

    @contextmanager
    def track(self, client, category):
        """Wrap one synchronous SDK instance temporarily; preserve its result."""
        original = client.responses.create

        def create(**kwargs):
            model = kwargs.get("model")
            if model not in PRICING:
                self.stopped = True
                raise CostBudgetExceeded("No verified price for the requested model")
            # Conservative byte-count allowance for text input plus schema and
            # request framing; not a billed token count or a tokenizer claim.
            input_allowance = len(json.dumps(kwargs, ensure_ascii=False).encode("utf-8")) + 4096
            reserve = estimate_cost(model, input_allowance, kwargs.get("max_output_tokens", 0), 0)
            if reserve is None or self.reserved_usd + reserve > self.budget_usd:
                self.stopped = True
                raise CostBudgetExceeded("Estimated API budget would be exceeded")
            started = time.perf_counter()
            row = dict(category=category, model=model, input_tokens=None, output_tokens=None,
                       cached_input_tokens=None, estimated_usd=None, preflight_reserve_usd=reserve,
                       status="request_failed")
            # Persist reservation before sending, including interrupted requests.
            self._save(dict(row, status="reserved"))
            try:
                raw = original(**kwargs)
                usage = getattr(raw, "usage", None)
                row.update(status=getattr(raw, "status", "unknown"), response_id=getattr(raw, "id", None),
                           reported_model=getattr(raw, "model", None))
                if usage is not None:
                    row["input_tokens"] = getattr(usage, "input_tokens", None)
                    row["output_tokens"] = getattr(usage, "output_tokens", None)
                    row["cached_input_tokens"] = getattr(getattr(usage, "input_tokens_details", None), "cached_tokens", None)
                    row["estimated_usd"] = estimate_cost(model, row["input_tokens"], row["output_tokens"], row["cached_input_tokens"])
                return raw
            finally:
                row["latency_seconds"] = time.perf_counter() - started
                # A final event replaces the reserved event when loading/reporting.
                row["request_number"] = len(self.requests())
                self._save(row)

        client.responses.create = create
        try:
            yield
        finally:
            client.responses.create = original

    def requests(self):
        """Fold reservation/completion events; an interrupted reserve stays unknown."""
        result = []
        for row in self.rows:
            if row["status"] == "reserved":
                result.append(row)
            else:
                result[row["request_number"] - 1] = row
        return result

    def summary(self, questions, judged):
        requests = self.requests()
        groups = {}
        for category in sorted({r["category"] for r in requests}):
            rows = [r for r in requests if r["category"] == category]
            known = [r["estimated_usd"] for r in rows if r["estimated_usd"] is not None]
            groups[category] = {"requests": len(rows), "estimated_usd": sum(known) if len(known) == len(rows) else None,
                                "known_cost_subtotal_usd": sum(known),
                                "models": sorted({r["model"] for r in rows})}
            denominator = judged if category == "judge" else questions
            groups[category]["mean_cost_per_question_usd"] = (
                sum(known) / denominator if len(known) == len(rows) and denominator else None)
            groups[category]["question_denominator"] = denominator
            for field in ("input_tokens", "output_tokens", "cached_input_tokens"):
                values = [r[field] for r in rows if r[field] is not None]
                groups[category][field] = sum(values) if len(values) == len(rows) else None
        known = [r["estimated_usd"] for r in requests if r["estimated_usd"] is not None]
        total = sum(known) if len(known) == len(requests) else None
        production = [r for r in requests if r["category"] in {"generation", "generation_repair"}]
        generation = sum(r["estimated_usd"] for r in production) if all(r["estimated_usd"] is not None for r in production) else None
        judge_rows = [r for r in requests if r["category"] == "judge"]
        judge_cost = sum(r["estimated_usd"] for r in judge_rows) if all(r["estimated_usd"] is not None for r in judge_rows) else None
        per_question = generation / questions if generation is not None and questions else None
        return dict(price_as_of="2026-11-02", prices_per_million=PRICING, sources=PRICE_SOURCES,
                    pricing_scope="Standard text tokens; estimates, not an account billing statement",
                    categories=groups, total_estimated_usd=total, known_cost_subtotal_usd=sum(known),
                    generation_per_question_usd=per_question,
                    judge_per_successfully_judged_question_usd=judge_cost / judged if judge_cost is not None and judged else None,
                    evaluation_per_question_usd=total / questions if total is not None and questions else None,
                    production_projection_usd={str(n): per_question * n if per_question is not None else None for n in (100, 10000)},
                    projection_assumption="Same question mix, repair frequency, usage and cached-token fraction; no production judging",
                    budget_usd=self.budget_usd, budget_stopped=self.stopped)
