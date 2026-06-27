"""Jira REST backend smoke test (live).

Pre-flights config, then exercises the M1 gateway against live Jira: whoami + the Phase-1 JQL.
Never prints the API token.

    python scripts/jira_smoke.py        # from engine/, with JIRA_* in env or engine/.env

Exit codes: 0 connected | 2 not configured | 3 auth failed (401/403) | 4 other Jira error | 1 unexpected.
"""
from __future__ import annotations

import sys

from qa_agent.config import TenantConfig
from qa_agent.jira import constants
from qa_agent.jira.config import JiraConfig, verify_config
from qa_agent.jira.rest_client import JiraError, JiraRestClient
from qa_agent.tenant import TenantContext


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass

    print("== Jira pre-flight ==")
    status = verify_config()
    for name, present in status.items():
        print(f"  {'set    ' if present else 'MISSING'}  {name}")
    if not all(status.values()):
        print("\nNot fully configured - set the MISSING value(s) in engine/.env.")
        return 2

    cfg = JiraConfig.from_env()
    tenant_id = cfg.project_key.lower()
    tcfg = TenantConfig(
        tenant_id=tenant_id,
        jira_base_url=cfg.base_url,
        allowed_project_keys=(cfg.project_key,),
    )
    tenant = TenantContext(tenant_id)

    print("\n== Live check ==")
    try:
        with JiraRestClient(tcfg, cfg) as client:
            me = client.myself(tenant)
            print(f"  connected OK as {me.get('displayName')} <{me.get('emailAddress', '?')}>")
            jql = constants.phase1_jql(cfg.project_key)
            issues = client.search_jql(tenant, jql, list(constants.FETCH_FIELDS))
            print(f"  Phase-1 JQL matched {len(issues)} ticket(s):")
            for issue in issues:
                fields = issue.get("fields", {})
                labels = fields.get("labels", [])
                print(f"    {issue.get('key')} - {fields.get('summary')}  [labels={labels}]")
        return 0
    except JiraError as exc:
        if exc.status in (401, 403):
            print(f"  AUTH FAILED ({exc.status}) - wiring OK, credentials rejected:\n  {exc}")
            return 3
        print(f"  Jira call rejected:\n  {exc}")
        return 4


if __name__ == "__main__":
    sys.exit(main())
