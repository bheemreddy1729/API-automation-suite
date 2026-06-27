"""The QA loop as a stateful graph (LangGraph). Phases mirror ``/ready-for-testing``.

This is the orchestration skeleton: each phase is a node, every node is tenant-scoped. LangGraph
is imported lazily (inside ``build_graph``) so the core package stays import-light and the
isolation tests run without it. Execution itself is FEDERATED to the team's CI (§9.3) — the
``dispatch_execution`` node triggers the team's pipeline; the engine never runs the tests.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .tenant import TenantContext, require_tenant


@dataclass
class LoopState:
    tenant: TenantContext
    ticket_key: str | None = None
    verdict: str | None = None             # SUFFICIENT | INSUFFICIENT | ERROR
    test_language: str = "python"          # resolved at plan start (gate input; default python)
    plan: dict[str, Any] | None = None
    approved: bool = False                 # human gate result
    results: dict[str, Any] | None = None


# --- phase nodes (tenant-scoped stubs; Phase 1 TODO) -------------------------
def fetch(state: LoopState) -> LoopState:
    require_tenant(state.tenant)
    raise NotImplementedError("fetch: timestamp-aware JQL via JiraGateway")


def context_check(state: LoopState) -> LoopState:
    require_tenant(state.tenant)
    raise NotImplementedError("context_check: classification model via the router")


def plan_gate(state: LoopState) -> LoopState:
    # Human gate (in Jira). Also where the test-script language is confirmed (default python).
    require_tenant(state.tenant)
    raise NotImplementedError("plan_gate: generate plan + QA-lead approve/edit/reject")


def generate(state: LoopState) -> LoopState:
    require_tenant(state.tenant)
    raise NotImplementedError("generate: get_generator(state.test_language) + coding model")


def dispatch_execution(state: LoopState) -> LoopState:
    # Federated execution (§9.3): trigger the team's GitHub Actions workflow. We do NOT run tests here.
    require_tenant(state.tenant)
    raise NotImplementedError("dispatch_execution: trigger the team CI workflow_dispatch")


def publish_results(state: LoopState) -> LoopState:
    require_tenant(state.tenant)
    raise NotImplementedError("publish_results: update Jira/Xray, transition card, comment")


def build_graph():
    """Wire the phases into a LangGraph ``StateGraph`` (lazy import)."""
    from langgraph.graph import END, StateGraph

    g = StateGraph(LoopState)
    g.add_node("fetch", fetch)
    g.add_node("context_check", context_check)
    g.add_node("plan_gate", plan_gate)
    g.add_node("generate", generate)
    g.add_node("dispatch_execution", dispatch_execution)
    g.add_node("publish_results", publish_results)
    g.set_entry_point("fetch")
    g.add_edge("fetch", "context_check")
    g.add_edge("context_check", "plan_gate")
    g.add_edge("plan_gate", "generate")
    g.add_edge("generate", "dispatch_execution")
    g.add_edge("dispatch_execution", "publish_results")
    g.add_edge("publish_results", END)
    return g.compile()
