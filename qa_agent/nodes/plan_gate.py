"""plan_gate — build the test plan, post it to Jira, and interrupt for headless human approval."""
from __future__ import annotations

from ..state import LoopState
from ..tenant import require_tenant


def plan_gate(state: LoopState) -> LoopState:
    # Human gate (Jira-driven). Also where the test-script language is confirmed (default python).
    require_tenant(state.tenant)
    raise NotImplementedError("plan_gate: generate plan + post to Jira + interrupt/resume on approval (M3)")
