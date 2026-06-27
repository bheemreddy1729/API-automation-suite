"""Pluggable per-stack test generators (§6). Default = python/pytest.

The target language is resolved at plan start (``resolve_test_language``); the registry maps a
language to its generator. MVP ships the python generator; other stacks slot in without engine
changes (engine language != generated-test language).
"""
from __future__ import annotations

from typing import Protocol

from ..tenant import TenantContext


class TestGenerator(Protocol):
    language: str

    def generate(self, tenant: TenantContext, plan: dict) -> dict: ...


class PytestGenerator:
    """Default generator (python/pytest). Skeleton — real generation calls the model router."""

    language = "python"

    def generate(self, tenant: TenantContext, plan: dict) -> dict:
        raise NotImplementedError(
            "PytestGenerator.generate — Phase 1 TODO (calls the coding model via the router)"
        )


_REGISTRY: dict[str, TestGenerator] = {}


def register(generator: TestGenerator) -> None:
    _REGISTRY[generator.language] = generator


def get_generator(language: str) -> TestGenerator:
    try:
        return _REGISTRY[language]
    except KeyError:
        raise ValueError(
            f"no generator registered for language {language!r} (have: {sorted(_REGISTRY)})"
        ) from None


register(PytestGenerator())  # default stack
