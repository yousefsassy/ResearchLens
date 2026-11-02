"""Lazy exports keep schema-only UI clients independent of inference libraries."""
from importlib import import_module

_EXPORTS = {"OpenAIClient": ".client", "GenerationConfig": ".config",
            "ResearchGenerator": ".generator", "GenerationResponse": ".schemas"}
__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    value = getattr(import_module(_EXPORTS[name], __name__), name)
    globals()[name] = value
    return value
