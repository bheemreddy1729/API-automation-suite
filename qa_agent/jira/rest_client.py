"""Jira Cloud REST v3 backend for :class:`JiraGateway` (headless / service-account path).

A Python port of the proven Java ``com.laerdal.api.jira.JiraClient``: HTTP Basic auth (account
email + API token) over ``httpx`` (already a dependency); no MCP, no extra HTTP dep. Covers exactly
the operations the LBVOICESER QA loop needs — whoami, JQL search (enhanced ``/search/jql`` with
``nextPageToken`` pagination), get issue, add comment (ADF), add/remove labels, create issue, link
issues, and read/apply transitions.

**Tenant isolation (§9.1):** the client is bound to ONE tenant (its :class:`TenantConfig`). Every
method takes a :class:`TenantContext` that must match the bound tenant, and write/create ops enforce
the per-tenant project boundary via :func:`assert_project_allowed`. Search is the caller's
responsibility to scope (the fetch node builds project-scoped JQL).
"""
from __future__ import annotations

import base64
from typing import Any

import httpx

from ..config import TenantConfig, assert_project_allowed
from ..tenant import CrossTenantError, TenantContext, require_tenant
from . import adf
from .config import JiraConfig


class JiraError(RuntimeError):
    """A Jira REST call failed (non-2xx, transport error, or unparseable body)."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class JiraRestClient:
    """REST implementation of :class:`qa_agent.jira.client.JiraGateway`, bound to one tenant."""

    def __init__(
        self,
        tenant_config: TenantConfig,
        jira: JiraConfig,
        *,
        client: httpx.Client | None = None,
    ) -> None:
        jira.require_credentials()
        self._tcfg = tenant_config
        self._base_url = (jira.base_url or tenant_config.jira_base_url).rstrip("/")
        creds = f"{jira.email}:{jira.api_token}".encode("utf-8")
        self._auth_header = "Basic " + base64.b64encode(creds).decode("ascii")
        self._client = client or httpx.Client(
            timeout=jira.timeout_ms / 1000.0,
            headers={"Authorization": self._auth_header, "Accept": "application/json"},
        )

    @classmethod
    def from_env(cls, tenant_config: TenantConfig, *, client: httpx.Client | None = None) -> "JiraRestClient":
        """Build from ``engine/.env`` / environment (Jira creds + base url)."""
        return cls(tenant_config, JiraConfig.from_env(), client=client)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "JiraRestClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # ---------------------------------------------------------------- guards
    def _guard(self, tenant: TenantContext | None, project_key: str | None = None) -> None:
        require_tenant(tenant)
        if tenant.tenant_id != self._tcfg.tenant_id:
            raise CrossTenantError(
                f"client is bound to tenant {self._tcfg.tenant_id!r} but got {tenant.tenant_id!r}"
            )
        if project_key is not None:
            assert_project_allowed(self._tcfg, project_key)

    @staticmethod
    def _project_of(issue_key: str) -> str:
        """``LBVOICESER-1335`` -> ``LBVOICESER`` (project boundary check on a single issue)."""
        return issue_key.split("-", 1)[0] if "-" in issue_key else issue_key

    # ---------------------------------------------------------------- core HTTP
    def _send(self, method: str, path: str, json_body: dict[str, Any] | None = None) -> Any:
        try:
            resp = self._client.request(method, self._base_url + path, json=json_body)
        except httpx.HTTPError as exc:
            raise JiraError(f"{method} {path} failed: {exc}") from exc
        if not (200 <= resp.status_code < 300):
            raise JiraError(
                f"{method} {path} -> HTTP {resp.status_code}: {resp.text[:500]}", resp.status_code
            )
        if not resp.content:
            return None
        try:
            return resp.json()
        except ValueError as exc:
            raise JiraError(f"Failed to parse response from {path}") from exc

    # ---------------------------------------------------------------- connectivity
    def myself(self, tenant: TenantContext) -> dict[str, Any]:
        """``GET /myself`` — verifies credentials; returns the current user."""
        self._guard(tenant)
        return self._send("GET", "/rest/api/3/myself")

    # ---------------------------------------------------------------- search
    def search_jql(self, tenant: TenantContext, jql: str, fields: list[str]) -> list[dict[str, Any]]:
        """All issues for ``jql``, following ``nextPageToken`` until exhausted.

        Read op: the caller must build tenant-scoped JQL (the fetch node uses the tenant's project).
        """
        self._guard(tenant)
        all_issues: list[dict[str, Any]] = []
        token: str | None = None
        while True:
            body: dict[str, Any] = {"jql": jql, "maxResults": 100}
            if fields:
                body["fields"] = list(fields)
            if token:
                body["nextPageToken"] = token
            resp = self._send("POST", "/rest/api/3/search/jql", body) or {}
            all_issues.extend(resp.get("issues", []))
            token = resp.get("nextPageToken")
            if not token:
                return all_issues

    # ---------------------------------------------------------------- issue read
    def get_issue(self, tenant: TenantContext, key: str, fields: list[str]) -> dict[str, Any]:
        self._guard(tenant, self._project_of(key))
        query = f"?fields={','.join(fields)}" if fields else ""
        return self._send("GET", f"/rest/api/3/issue/{key}{query}")

    # ---------------------------------------------------------------- comments
    def add_comment(self, tenant: TenantContext, key: str, body: str) -> None:
        self._guard(tenant, self._project_of(key))
        self._send("POST", f"/rest/api/3/issue/{key}/comment", {"body": adf.from_plain_text(body)})

    # ---------------------------------------------------------------- labels
    def set_labels(
        self, tenant: TenantContext, key: str, add: list[str], remove: list[str]
    ) -> None:
        """Add/remove labels without disturbing the others (``update.labels`` ops)."""
        self._guard(tenant, self._project_of(key))
        ops = [{"add": label} for label in (add or [])] + [
            {"remove": label} for label in (remove or [])
        ]
        if not ops:
            return
        self._send("PUT", f"/rest/api/3/issue/{key}", {"update": {"labels": ops}})

    # ---------------------------------------------------------------- create issue
    def create_issue(
        self,
        tenant: TenantContext,
        project_key: str,
        issue_type: str,
        summary: str,
        description: str | None = None,
    ) -> str:
        """Create an issue (project key + issue type name + summary required). Returns the new key."""
        self._guard(tenant, project_key)
        fields: dict[str, Any] = {
            "project": {"key": project_key},
            "issuetype": {"name": issue_type},
            "summary": summary,
        }
        if description:
            fields["description"] = adf.from_plain_text(description)
        resp = self._send("POST", "/rest/api/3/issue", {"fields": fields})
        return resp["key"]

    # ---------------------------------------------------------------- issue links
    def create_issue_link(
        self, tenant: TenantContext, type_name: str, inward_key: str, outward_key: str
    ) -> None:
        """Link two issues. For ``Tests``: inward=Test card, outward=parent."""
        self._guard(tenant, self._project_of(inward_key))
        assert_project_allowed(self._tcfg, self._project_of(outward_key))
        self._send(
            "POST",
            "/rest/api/3/issueLink",
            {
                "type": {"name": type_name},
                "inwardIssue": {"key": inward_key},
                "outwardIssue": {"key": outward_key},
            },
        )

    # ---------------------------------------------------------------- transitions
    def get_transitions(self, tenant: TenantContext, key: str) -> list[dict[str, str]]:
        """Transitions available from the issue's current status (id + name)."""
        self._guard(tenant, self._project_of(key))
        resp = self._send("GET", f"/rest/api/3/issue/{key}/transitions") or {}
        return [{"id": t["id"], "name": t["name"]} for t in resp.get("transitions", [])]

    def find_transition(self, tenant: TenantContext, key: str, name: str) -> dict[str, str] | None:
        """Resolve a transition by case-insensitive name; None if not reachable now."""
        for t in self.get_transitions(tenant, key):
            if t["name"].lower() == name.lower():
                return t
        return None

    def transition(self, tenant: TenantContext, key: str, transition_id: str) -> None:
        self._guard(tenant, self._project_of(key))
        self._send(
            "POST", f"/rest/api/3/issue/{key}/transitions", {"transition": {"id": transition_id}}
        )
