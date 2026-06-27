"""Task-aware model router (§6) — model- and vendor-agnostic.

The engine never hardcodes a model; it asks the router per task. MVP = a simple rule-based
policy over a couple of models; richer routing is roadmap (§12). Sensitive tenants route to an
in-region model (ties to §9.1 per-tenant data-handling).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class TaskKind(str, Enum):
    CODE_GENERATION = "code_generation"   # test/code authoring  -> coding model
    REASONING = "reasoning"               # gate decisions, spec-vs-behavior -> reasoning model
    CLASSIFICATION = "classification"     # cheap verdicts (context-check) -> small/fast model


@dataclass(frozen=True, slots=True)
class ModelSpec:
    provider: str           # e.g. "azure_openai" (lead candidate), "anthropic", ...
    model: str
    in_region: bool = False


class ModelRouter(Protocol):
    def select(self, task: TaskKind, *, sensitive: bool = False) -> ModelSpec: ...


@dataclass
class RuleBasedRouter:
    """Config-driven default policy. Swap providers/models without touching call sites."""

    coding: ModelSpec
    reasoning: ModelSpec
    classification: ModelSpec
    in_region_override: ModelSpec | None = None   # used when sensitive=True

    def select(self, task: TaskKind, *, sensitive: bool = False) -> ModelSpec:
        if sensitive and self.in_region_override is not None:
            return self.in_region_override
        return {
            TaskKind.CODE_GENERATION: self.coding,
            TaskKind.REASONING: self.reasoning,
            TaskKind.CLASSIFICATION: self.classification,
        }[task]
