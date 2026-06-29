"""Enterprise QA Agent engine — central brain (Phase 1 scaffold).

Architecture: ../../docs/enterprise-qa-agent-platform.md. The one principle baked in from
line one: every tenant-scoped operation REQUIRES an explicit TenantContext (structural
isolation, §9.1 rule 1) — there is no ambient/default tenant.
"""

from .config import TenantConfig
from .tenant import TenantContext

__all__ = ["TenantContext", "TenantConfig"]
