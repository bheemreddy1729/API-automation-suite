"""story_update — INSUFFICIENT path: post the context-request comment + label (label-first, comment-last)."""
from __future__ import annotations

from ..state import LoopState
from ..tenant import require_tenant


def story_update(state: LoopState) -> LoopState:
    require_tenant(state.tenant)
    raise NotImplementedError("story_update: label-first/comment-last with the context-request sentinel (M2)")
