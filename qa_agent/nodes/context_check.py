"""context_check — score requirement readiness (SUFFICIENT/INSUFFICIENT) via the classification model."""
from __future__ import annotations

from ..state import LoopState
from ..tenant import require_tenant


def context_check(state: LoopState) -> LoopState:
    require_tenant(state.tenant)
    raise NotImplementedError("context_check: classification model via the router (M2)")
