"""The QA loop as a LangGraph ``StateGraph``. Phases mirror ``/ready-for-testing``.

Conventional LangGraph layout: state lives in ``state.py``, phase functions in ``nodes/``, routing
in ``edges.py``; this module just *assembles* them and exposes a compiled ``graph`` instance for
``langgraph.json`` (LangGraph Platform / ``langgraph dev``). Every node is tenant-scoped, and
execution FEDERATES to the team's CI (§9.3) — ``dispatch_execution`` triggers the team's pipeline;
the engine never runs the tests.
"""
from __future__ import annotations

from langgraph.graph import END, StateGraph

from . import nodes
from .edges import route_after_context_check
from .state import LoopState


def build_graph(*, checkpointer=None):
    """Wire the phases into a compiled ``StateGraph``.

    SUFFICIENT tickets flow fetch → context_check → plan_gate → generate → dispatch_execution →
    publish_results; INSUFFICIENT/ERROR branch to story_update and end. Pass a ``checkpointer``
    (M3) to persist state across runs for the headless Jira-driven gates.
    """
    g = StateGraph(LoopState)
    g.add_node("fetch", nodes.fetch)
    g.add_node("context_check", nodes.context_check)
    g.add_node("story_update", nodes.story_update)
    g.add_node("plan_gate", nodes.plan_gate)
    g.add_node("generate", nodes.generate)
    g.add_node("dispatch_execution", nodes.dispatch_execution)
    g.add_node("publish_results", nodes.publish_results)

    g.set_entry_point("fetch")
    g.add_edge("fetch", "context_check")
    g.add_conditional_edges(
        "context_check",
        route_after_context_check,
        {"plan_gate": "plan_gate", "story_update": "story_update"},
    )
    g.add_edge("story_update", END)            # insufficient: comment posted, await the author
    g.add_edge("plan_gate", "generate")
    g.add_edge("generate", "dispatch_execution")
    g.add_edge("dispatch_execution", "publish_results")
    g.add_edge("publish_results", END)
    return g.compile(checkpointer=checkpointer)


# Compiled instance referenced by langgraph.json (LangGraph Platform / `langgraph dev`).
graph = build_graph()
