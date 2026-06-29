"""Per-tenant configuration + test-language resolution.

Tenancy is DATA, not code (§9.2): a tenant is a config record, added live — never a subclass
or a separate deploy. The target test-script language resolves (round 10):
    explicit plan-start choice  →  per-tenant config  →  global default ("python").
"""
from __future__ import annotations

from dataclasses import dataclass

from .tenant import CrossTenantError, TenantContext

DEFAULT_TEST_LANGUAGE = "python"  # global default (round 10); per-tenant config may override


@dataclass(frozen=True, slots=True)
class TenantConfig:
    """A tenant = one config record. Customization is config, not inheritance (§9.2)."""

    tenant_id: str
    jira_base_url: str
    allowed_project_keys: tuple[str, ...]            # per-tenant execution boundary (§9.1 rule 3)
    trigger_status: str = "Ready for testing"
    default_test_language: str | None = None          # overrides the global default if set
    prompt_overlay: str = ""                           # tunable area ONLY (§9.2 guardrails)

    def context(self) -> TenantContext:
        return TenantContext(self.tenant_id)


def resolve_test_language(explicit: str | None, cfg: TenantConfig | None) -> str:
    """explicit choice → per-tenant config → global default (python)."""
    if explicit and explicit.strip():
        return explicit.strip().lower()
    if cfg and cfg.default_test_language:
        return cfg.default_test_language.strip().lower()
    return DEFAULT_TEST_LANGUAGE


def assert_project_allowed(cfg: TenantConfig, project_key: str) -> None:
    """Enforce the per-tenant execution boundary: a tenant may touch only its own projects."""
    if project_key not in cfg.allowed_project_keys:
        raise CrossTenantError(
            f"tenant {cfg.tenant_id!r} is not permitted to touch project {project_key!r}"
        )
