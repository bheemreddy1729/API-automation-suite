"""publish_results — create/link the Xray Test card, transition it, comment, label parent on all-pass."""
from __future__ import annotations

from ..state import LoopState
from ..tenant import require_tenant


def publish_results(state: LoopState) -> LoopState:
    require_tenant(state.tenant)
    raise NotImplementedError("publish_results: JUnit XML -> Xray, transition card, comment, label parent (M4)")
