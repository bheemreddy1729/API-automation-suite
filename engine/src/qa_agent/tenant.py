"""TenantContext — the structural isolation boundary (§9.1 rule 1).

Every call that touches Jira / MCP / CI / secrets must carry an explicit TenantContext.
There is no default/ambient tenant: constructing one without an id fails immediately, so a
missing tenant is a hard error (caught in tests/CI), never a silent cross-tenant leak.
"""
from __future__ import annotations

from dataclasses import dataclass


class CrossTenantError(RuntimeError):
    """Raised when an operation for one tenant reaches another tenant's resources."""


@dataclass(frozen=True, slots=True)
class TenantContext:
    """Immutable identity carried on every boundary call. ``tenant_id`` is mandatory."""

    tenant_id: str

    def __post_init__(self) -> None:
        if not self.tenant_id or not self.tenant_id.strip():
            raise ValueError("TenantContext requires a non-empty tenant_id (no default tenant).")


def require_tenant(tenant: TenantContext | None) -> TenantContext:
    """Guard for boundary calls: reject a missing tenant rather than defaulting one."""
    if tenant is None:
        raise ValueError("a TenantContext is required for this operation (no ambient tenant).")
    return tenant
