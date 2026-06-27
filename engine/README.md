# QA Agent Engine (Phase 1 scaffold)

The central **brain** of the Enterprise QA Agent platform — model- & framework-agnostic,
Python + LangGraph. Architecture: [../docs/enterprise-qa-agent-platform.md](../docs/enterprise-qa-agent-platform.md).

> **Phase 1 scaffold.** Establishes the structure and the **tenant-isolation boundary first**
> (the slice all three review models agreed on). Phase logic is stubbed with explicit TODOs; the
> isolation tests are real and pass.

## Layout

| Module | Role |
|---|---|
| `qa_agent/tenant.py` | `TenantContext` — required `tenant_id`, **no default tenant** (§9.1 rule 1) |
| `qa_agent/config.py` | per-tenant config (**data, not subclasses** §9.2); test-language resolution (default **python**); per-tenant project boundary |
| `qa_agent/models/router.py` | task-aware **model router** (coding / reasoning / classification; in-region for sensitive) — model-agnostic (§6) |
| `qa_agent/jira/client.py` | `JiraGateway` protocol — one tenant-scoped interface over REST (headless) + Rovo MCP (interactive) (§5) |
| `qa_agent/generation/` | pluggable per-stack generators; default `python/pytest` (§6) |
| `qa_agent/graph.py` | the loop as a LangGraph state graph; execution **federates** to the team CI (§9.3) |
| `tests/test_tenant_isolation.py` | structural isolation proof (§9.1 rules 1, 3, 7) |

## Run the isolation tests

```sh
python tests/test_tenant_isolation.py        # no deps beyond stdlib
# or, with the toolchain:
pip install -e ".[dev]" && pytest
```

## Not built yet (Phase 1 TODO)

The phase nodes (`fetch` / `context_check` / `plan_gate` / `generate` / `dispatch_execution` /
`publish_results`) are stubs. Wiring them needs: the chosen model behind the router, a Jira REST
impl (Python port of the Java `JiraClient`) + the Rovo MCP client, and the GitHub Actions dispatch
for federated execution. The auth mode (API token vs OAuth) depends on the `JiraConnectionIT`
smoke-test result — does SSO permit API tokens.
