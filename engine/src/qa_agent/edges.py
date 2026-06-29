"""Edge / routing logic for the QA loop (LangGraph convention: routing lives in its own module)."""
from __future__ import annotations

from typing import Literal

from .state import LoopState


def route_after_context_check(state: LoopState) -> Literal["plan_gate", "story_update"]:
    """SUFFICIENT proceeds to planning; INSUFFICIENT/ERROR take the context-request path.

    ``context_check`` sets ``state.verdict``. Anything other than SUFFICIENT routes to
    ``story_update`` (post the insufficient comment + label, then end this ticket).
    """
    return "plan_gate" if state.verdict == "SUFFICIENT" else "story_update"
