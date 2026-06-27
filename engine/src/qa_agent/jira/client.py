"""Jira access behind one tenant-scoped interface (§5).

Two backends will implement this protocol: a REST client (headless / service-account — a Python
port of the proven Java ``JiraClient``) and a Rovo MCP client (interactive / act-as-user). The
orchestrator picks an *identity mode*, never "MCP vs REST". EVERY method takes a TenantContext —
no ambient tenant (§9.1 rule 1).
"""
from __future__ import annotations

from typing import Any, Protocol

from ..tenant import TenantContext


class JiraGateway(Protocol):
    """All operations are tenant-scoped by signature (structural isolation).

    Backends: :class:`qa_agent.jira.rest_client.JiraRestClient` (headless, the autonomous loop) and
    a future Rovo MCP client (interactive / act-as-user) — same contract, swappable.
    """

    def myself(self, tenant: TenantContext) -> dict[str, Any]: ...

    def search_jql(self, tenant: TenantContext, jql: str, fields: list[str]) -> list[dict[str, Any]]: ...

    def get_issue(self, tenant: TenantContext, key: str, fields: list[str]) -> dict[str, Any]: ...

    def add_comment(self, tenant: TenantContext, key: str, body: str) -> None: ...

    def set_labels(self, tenant: TenantContext, key: str, add: list[str], remove: list[str]) -> None: ...

    def create_issue(
        self,
        tenant: TenantContext,
        project_key: str,
        issue_type: str,
        summary: str,
        description: str | None = None,
    ) -> str: ...

    def create_issue_link(
        self, tenant: TenantContext, type_name: str, inward_key: str, outward_key: str
    ) -> None: ...

    def get_transitions(self, tenant: TenantContext, key: str) -> list[dict[str, str]]: ...

    def find_transition(
        self, tenant: TenantContext, key: str, name: str
    ) -> dict[str, str] | None: ...

    def transition(self, tenant: TenantContext, key: str, transition_id: str) -> None: ...
