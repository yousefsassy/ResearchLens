"""Opt-in, request-local timings. No prompt, query, or credential data is stored."""
from contextlib import contextmanager
from contextvars import ContextVar
from time import perf_counter

_active = ContextVar("researchlens_profile", default=None)


@contextmanager
def collect():
    values = {}
    token = _active.set(values)
    try:
        yield values
    finally:
        _active.reset(token)


@contextmanager
def measure(name):
    values = _active.get()
    if values is None:
        yield
        return
    started = perf_counter()
    try:
        yield
    finally:
        item = values.setdefault(name, {"seconds": 0.0, "calls": 0})
        item["seconds"] += perf_counter() - started
        item["calls"] += 1


def timed(name):
    from functools import wraps

    def decorate(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            with measure(name):
                return function(*args, **kwargs)
        return wrapped
    return decorate


def record_usage(name, metrics):
    """Attach per-request accounting to its timing entry, never request content."""
    values = _active.get()
    if values is not None:
        item = values.setdefault(name, {"seconds": 0.0, "calls": 0})
        item["usage"] = {key: getattr(metrics, key) for key in (
            "attempts", "prompt_tokens", "completion_tokens", "reasoning_tokens", "accounting_complete")}


def record_validation_failure(attempt, error):
    """Persist only a fixed category, never rejected text or provider payloads."""
    values = _active.get()
    if values is None:
        return
    category = "invalid_claim"
    for fragment, code in (("unknown source ID", "unknown_source"), ("empty citation quote", "empty_quote"),
                           ("quote not found", "quote_mismatch"), ("missing citations", "comparison_coverage")):
        if fragment in error:
            category = code
            break
    name = "repair_citation_validation" if attempt else "initial_citation_validation"
    item = values.setdefault(name, {"seconds": 0.0, "calls": 0})
    item["calls"] += 1
    item["failure_category"] = category
