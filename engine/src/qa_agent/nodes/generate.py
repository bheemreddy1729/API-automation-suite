"""generate — produce tests in the chosen stack (language-agnostic generator) + a run-manifest."""
from __future__ import annotations

from ..state import LoopState
from ..tenant import require_tenant


def generate(state: LoopState) -> LoopState:
    require_tenant(state.tenant)
    raise NotImplementedError("generate: get_generator(state.test_language) + coding model + run-manifest (M3)")
