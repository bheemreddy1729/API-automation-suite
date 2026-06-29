"""dispatch_execution — federate to the team's CI: PR the tests, workflow_dispatch, poll the run.

Federated execution (§9.3): we trigger the team's GitHub Actions workflow and never run tests here.
"""
from __future__ import annotations

from ..state import LoopState
from ..tenant import require_tenant


def dispatch_execution(state: LoopState) -> LoopState:
    require_tenant(state.tenant)
    raise NotImplementedError("dispatch_execution: PR into target repo + workflow_dispatch + poll (M4)")
