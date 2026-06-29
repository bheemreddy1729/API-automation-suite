"""Graph state for the QA loop (LangGraph convention: state lives in its own module).

LangGraph accepts a dataclass as the state schema. Every field a node reads/writes lives here;
the ``tenant`` is mandatory (structural isolation — there is no ambient tenant).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .tenant import TenantContext


@dataclass
class LoopState:
    tenant: TenantContext                       # required — the isolation boundary (§9.1)
    ticket_key: str | None = None
    verdict: str | None = None                  # SUFFICIENT | INSUFFICIENT | ERROR
    detected: dict[str, Any] | None = None      # context-check output (method/endpoint/ACs/missing)
    test_language: str = "python"               # resolved at plan start (gate input; default python)
    plan: dict[str, Any] | None = None
    approved: bool = False                      # human gate result (Jira-driven)
    test_card_key: str | None = None            # Xray Test card created/reused at publish
    run_id: str | None = None                   # federated CI run id (dispatch → poll)
    results: dict[str, Any] | None = None
    dry_run: bool = True                        # when True, nodes log intended writes but don't perform them
    notes: list[str] = field(default_factory=list)  # human-readable trace of what each node did
