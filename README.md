# QA Engine

The central **brain** of the Enterprise QA Agent platform — **Python + LangGraph**,
model- & framework-agnostic, multi-tenant, with **federated execution**.

This repo is the engine *only*. It does not contain a product test suite: it reads a team's
Jira tickets, checks requirement readiness, generates tests in the team's chosen stack, and
**dispatches them to run in that team's own GitHub repo/CI** — then publishes results back to
Jira/Xray. The engine never holds a team's source code, secrets, or runtime (§9.3).

## What it does (the loop)
`fetch` (Jira "Ready for testing") → `context_check` (requirements sufficient?) → `plan_gate`
(test plan, human-approved in Jira) → `generate` (tests in the chosen language) →
`dispatch_execution` (trigger the team's CI) → `publish_results` (Xray Test card, transitions,
comments). Gates are **headless and Jira-driven**; results are reported as **JUnit XML → Xray**.

## Layout
- `engine/` — the Python engine (see [engine/README.md](engine/README.md)). Start here.
- `docs/` — architecture & decisions ([enterprise-qa-agent-platform.md](docs/enterprise-qa-agent-platform.md)),
  Jira ground truth, history.
- `.claude/` — the proven loop logic as prompts/commands (the spec the engine ports).
- `experiments/` — feasibility probes (e.g. Rovo MCP consumption).
- `scripts/` — Xray auth/import references (used by the federated runner).

## Getting started
```sh
cd engine
python -m venv .venv && . .venv/Scripts/activate    # Windows; use bin/activate on POSIX
pip install -e ".[dev]"
pytest                                               # structural-isolation tests
```
Fill `engine/.env` from `engine/.env.example` (git-ignored) for live Azure/Jira/GitHub access.

## Identity & config
A team is onboarded as a `TenantConfig` record (Jira project + target repo + language + credential
refs) — config, not code. MVP identity is **user-role assumption** (the QA lead's Jira API token +
a user GitHub PAT); a governed service account comes later.

## History
The former Java/REST-Assured TTS test suite was removed when this repo became the engine — see
[docs/java-suite-history.md](docs/java-suite-history.md).
