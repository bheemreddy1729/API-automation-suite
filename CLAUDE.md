# CLAUDE.md — conventions for the QA Engine repo

This repo is the **QA Engine** (the central "brain") of the Enterprise QA Agent platform:
**Python + LangGraph**, model- & framework-agnostic, multi-tenant, with **federated execution**.
It does NOT contain a product test suite — it *generates* tests and dispatches them to run in
each team's own repo/CI. Architecture: [docs/enterprise-qa-agent-platform.md](docs/enterprise-qa-agent-platform.md).
Overview: [README.md](README.md).

> The Java/REST-Assured TTS test suite that used to live here was removed when this repo became
> the engine — see [docs/java-suite-history.md](docs/java-suite-history.md) for recovery refs.

## Architecture: a durable workflow, not a multi-agent system
By the autonomy test (*who decides the next step?*), this is a **workflow**: we control the phase
order; the model is called *within* fixed steps (classification, generation) — it does not choose
what to do next. So it's a LangGraph **graph/pipeline** with deterministic gates — not a single
free-running "agent" and not multi-agent. Stay left on the spectrum (workflow → agent → multi-agent;
each step right costs ~4–15× more). Engineering rules we hold to:
- **Thin nodes, heavy tools:** nodes decide/sequence; tools (`JiraGateway`, generators, `exec/`) do
  the mechanics + deterministic rules, returning structured output + actionable errors.
- **Durable execution + HITL:** LangGraph + a checkpointer for pause/resume at the Jira-driven gates.
- **Validation loops:** generate → validate (hard checks: compile/collect, runner preflight) → fix.
- **Observability:** trace each run's steps/decisions/token costs (`LoopState.notes`; Studio via `langgraph dev`).
- **Models by step difficulty:** cheap model for classification, stronger for planning/generation (the router).

## Commands (run from the repo root)
- `pip install -e ".[dev]"` — install the engine + dev tools into a venv (`.venv`).
- `pytest` (or `python tests/test_tenant_isolation.py`) — run engine unit/isolation tests.
- `langgraph dev` — local LangGraph dev server + Studio (reads `langgraph.json`; needs `.[dev]`).
- `python -m qa_agent.models.azure_openai` — Azure model pre-flight (booleans only, no secrets).
- `python scripts/azure_smoke.py` / `python scripts/jira_smoke.py` — live Azure / Jira smoke tests.

## Conventions
- **Config / secrets:** never hard-code endpoints, tokens, repos, or model names. Read everything
  from env / the git-ignored `.env` (loaded via `python-dotenv`). Secrets only via env vars
  / `.env`, never committed. Resolution mirrors the platform: `-D`/explicit → env var → `.env` → default.
- **Tenant isolation (§9.1):** every boundary call (Jira / GitHub / model / secrets) takes an
  explicit `TenantContext` — there is **no ambient/default tenant**. Enforce per-tenant project
  scope with `assert_project_allowed`. A missing tenant must fail loudly (tests guard this).
- **Tenancy is data, not code (§9.2):** a tenant is a `TenantConfig` record (Jira project, target
  repo, language, credential refs) — never a subclass or a separate deploy.
- **Jira access goes through `JiraGateway`** (`qa_agent/jira/client.py`). The autonomous loop uses
  the **REST backend** (headless, per-tenant token); **Rovo MCP** is the future interactive/
  act-as-user backend behind the same seam. Don't call Jira from nodes except via the gateway.
- **Models go through the router** (`qa_agent/models/router.py` → `build_chat_model`): pick a
  deployment by `TaskKind` (coding / reasoning / classification). Never hard-code a model.
- **Execution is federated (§9.3):** the engine generates tests and triggers the *team's* CI; it
  never runs product tests or holds a team's source/secrets. Results = **JUnit XML → Xray** (no Allure).
- **Identity (MVP):** user-role assumption — the QA lead's Jira API token + a user GitHub PAT. No
  service account yet.

## Structure (`qa_agent/` at the repo root)
Follows the standard LangGraph layout (state / nodes / edges / graph). `langgraph.json` points
`langgraph dev` / Platform at the compiled `graph` instance.
- `tenant.py` — `TenantContext` (required id, no default).
- `config.py` — `TenantConfig` + test-language resolution (default **python**) + project boundary.
- `state.py` — `LoopState` (the graph state schema).
- `nodes/` — one module per phase (`fetch`, `context_check`, `story_update`, `plan_gate`,
  `generate`, `dispatch_execution`, `publish_results`).
- `edges.py` — routing/conditional-edge logic (e.g. SUFFICIENT → plan_gate, else → story_update).
- `graph.py` — assembles the `StateGraph`; exports `build_graph()` + a compiled `graph` instance.
- `models/` — task-aware router + Azure backend (`build_chat_model`).
- `jira/` — `JiraGateway` protocol + REST backend (port of the proven Java client).
- `generation/` — pluggable per-stack generators (language chosen at generation time).
- `exec/` — GitHub dispatch/poll + Xray import.
Headless Jira-driven gates use LangGraph interrupt/resume with a checkpointer.

## Loop logic reference
The proven loop behavior (JQL, context-check scoring, insufficient-comment + sentinel, test-plan and
generation templates, Test-card creation/linking) is specified in `.claude/prompts/` and
`.claude/commands/`. The Python nodes reimplement that — keep them faithful to those specs and to the
verified Jira ground truth (status/label/ID strings).

## Test style (engine code)
- `pytest`, one behaviour per test; keep the structural-isolation tests green.
- No network in unit tests — stub the gateway / model; live checks are explicit smoke scripts.
