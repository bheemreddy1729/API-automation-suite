"""Structural tenant-isolation tests (§9.1 rules 1, 3, 7).

Proves isolation is enforced by construction, not convention:
  - no tenant can be constructed without an id (no default/ambient tenant);
  - boundary guards reject a missing tenant;
  - a tenant cannot reach another tenant's projects;
  - the test-script language resolves to the python default.

Runnable two ways:  python tests/test_tenant_isolation.py   |   pytest
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qa_agent.config import TenantConfig, assert_project_allowed, resolve_test_language
from qa_agent.tenant import CrossTenantError, TenantContext, require_tenant


def test_no_default_tenant():
    for bad in ("", "   "):
        try:
            TenantContext(bad)
        except ValueError:
            continue
        raise AssertionError("blank tenant_id must be rejected (no default tenant)")


def test_boundary_requires_tenant():
    try:
        require_tenant(None)
    except ValueError:
        pass
    else:
        raise AssertionError("require_tenant(None) must raise")
    assert require_tenant(TenantContext("lbvoiceser")).tenant_id == "lbvoiceser"


def test_cross_tenant_project_blocked():
    cfg = TenantConfig(
        tenant_id="lbvoiceser",
        jira_base_url="https://laerdal.atlassian.net",
        allowed_project_keys=("LBVOICESER",),
    )
    assert_project_allowed(cfg, "LBVOICESER")  # own project: ok
    try:
        assert_project_allowed(cfg, "OTHERTEAM")
    except CrossTenantError:
        pass
    else:
        raise AssertionError("touching another tenant's project must raise CrossTenantError")


def test_test_language_resolution_defaults_python():
    cfg_none = TenantConfig("t", "https://x", ("P",))
    assert resolve_test_language(None, cfg_none) == "python"        # global default
    assert resolve_test_language("java", cfg_none) == "java"        # explicit wins
    cfg_java = TenantConfig("t", "https://x", ("P",), default_test_language="java")
    assert resolve_test_language(None, cfg_java) == "java"          # per-tenant override
    assert resolve_test_language("python", cfg_java) == "python"    # explicit beats config


def _run_all() -> None:
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} isolation checks passed.")


if __name__ == "__main__":
    _run_all()
