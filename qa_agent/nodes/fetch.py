"""fetch — pull "Ready for testing" tickets via the JiraGateway (timestamp-aware Phase-1 JQL)."""
from __future__ import annotations

from ..state import LoopState
from ..tenant import require_tenant


def fetch(state: LoopState) -> LoopState:
    require_tenant(state.tenant)
    raise NotImplementedError("fetch: timestamp-aware JQL via JiraGateway (M2)")
