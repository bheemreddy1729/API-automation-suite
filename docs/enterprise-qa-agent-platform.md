# Enterprise QA Agent Platform — architecture & roadmap (v1 draft)

> **Status:** planning draft for review. Grounded in the connection experiments on
> branches `feature/jira-rest-connection` (direct REST client) and
> `feature/rovo-mcp-experiment` (proven custom-client MCP consumption).
> **Owner:** Praveen (Laerdal). **Last updated:** 2026-06-27.

## 1. Vision

Turn the single-project LBVOICESER QA loop into an **internal platform** that *any* team,
across *any* Jira project, can onboard to get AI-driven test automation: requirement
readiness-check → test-plan → human gate → test generation → run → Jira update with full
Xray traceability. Self-service for teams; governed and auditable for the org.

This is an agentic *product*, not a script — plan it with a product lifecycle (goal →
PRD → orchestration → autonomous run → eval → deploy → monitor). The transport question
(MCP vs REST) is **settled** (both work — see §5); the platform questions are identity,
multi-tenancy, hosting, and governance.

## 2. What's already proven (Phase 0 — done)

| Capability | Evidence |
|---|---|
| Direct Jira REST v3 + API token, headless | `com.laerdal.api.jira.JiraClient` compiles; `JiraConnectionIT` |
| Custom (non-Claude) agent can consume **Rovo MCP** | `experiments/rovo-mcp` probe: 31 tools, all 8 loop ops, write scope granted |
| Rovo MCP is GA with org governance | admin controls + permissions + audit logging + IP allowlist |

## 3. The decision that shapes everything: identity model

Three options; the platform should be **hybrid (recommended)**.

| Model | How | Pros | Cons | Use for |
|---|---|---|---|---|
| **Act-as-user** (OAuth 2.1 / 3LO) | Each employee consents once; agent acts with *their* Jira permissions; actions attributed to them | Least-privilege, correct attribution, respects per-project access — compliance-friendly | Per-user consent + token lifecycle; account-mapping | Interactive/attended use; cross-team self-service |
| **Service identity** (governed API token / service principal, project-scoped) | One (or per-team) bot identity with explicitly granted project permissions | Headless, simple, CI-friendly, predictable | Coarse permissions; attribution shows as the bot | Autonomous background loops (the Ready-for-testing cron) |
| **Per-tenant scoped credentials** | Each onboarded project gets its own scoped credential set, full isolation | Strong blast-radius isolation | More credential management | Strict-isolation teams |

**Recommendation:** **hybrid** — service identity for the autonomous loop (no human present),
act-as-user for interactive sessions and any write a person should own. Both are governed by
the org-admin Rovo MCP permissions + audit log, so security/compliance get one control plane.

## 4. Layered architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  Teams / Projects (LBVOICESER, …)  — self-service onboarding portal   │
├─────────────────────────────────────────────────────────────────────┤
│  Orchestration & agent runtime                                        │
│   • QA lifecycle as a hosted service (the /ready-for-testing phases)  │
│   • Claude Agent SDK based (MCP-native; matches what works today)     │
│   • Scheduler/queue for autonomous loops; stateless workers           │
│   • Human gates preserved (plan + script approvals) — non-negotiable  │
├─────────────────────────────────────────────────────────────────────┤
│  Jira integration layer (one internal abstraction, two backends)      │
│   • Rovo MCP  → act-as-user / interactive (tools for free, governed)  │
│   • REST (JiraClient) → service-identity / headless loops             │
├─────────────────────────────────────────────────────────────────────┤
│  Identity & secrets                                                   │
│   • Per-user OAuth tokens + service principals in a central vault     │
│     (Azure Key Vault assumed — confirm) ; token refresh & rotation    │
├─────────────────────────────────────────────────────────────────────┤
│  Config & multi-tenancy                                               │
│   • Per-project config: project key, trigger status, labels,          │
│     conventions, target test stack, traceability (Xray) settings      │
├─────────────────────────────────────────────────────────────────────┤
│  Governance & compliance (medical-grade)                              │
│   • Rovo MCP audit logs + IP allowlist + permission scoping           │
│   • Platform: per-tenant isolation, no auto-merge, full traceability  │
└─────────────────────────────────────────────────────────────────────┘
```

## 5. MCP vs REST — when each (resolved)

- **Rovo MCP via the agent runtime** for interactive/attended and act-as-user work: the
  31-tool surface comes for free, governed centrally. Don't hand-wrap tools.
- **REST (`JiraClient`)** for the autonomous, unattended loop where browser consent is
  impossible and a service identity is correct.
- One internal interface over both so the orchestration code doesn't care which backend ran.

## 6. The reasoning layer is still an LLM

Context-scoring and **test generation** remain Claude (API/Agent SDK) work — a deterministic
service can't generate tests. "Independent of Claude Code" = independent of the *CLI harness*,
not of the model. Generation is currently Java/JUnit/REST-Assured; going multi-team may mean
**polyglot generation** (other teams' stacks) — a major scope lever (see §8).

## 7. Phased roadmap (crawl → walk → run)

- **Phase 1 — Productionize for one team.** Host the LBVOICESER loop as a service:
  service-identity REST auth, scheduler for Ready-for-testing, human gates intact, results to
  Xray. *Goal: the loop runs without Claude Code.*
- **Phase 2 — Multi-project (same team).** Config-driven: onboard a 2nd/3rd project by config,
  not code. Prove the abstraction holds.
- **Phase 3 — Multi-team self-service.** Onboarding portal + admin approval flow; act-as-user
  OAuth; Rovo MCP governance wired in; audit/compliance review.
- **Phase 4 — Generalize the test stack** (only if demanded): polyglot generation, pluggable
  runners/reporters.

## 8. Open decisions (need you / the org)

1. **Atlassian org-admin support** — can you get an admin to enable + govern Rovo MCP and
   provision a service identity? (Gating for Phases 3.)
2. **Hosting** — internal cloud (Azure/Entra assumed), on-prem, or container platform?
3. **Compliance path** — what security review does a medical-device internal tool require, and
   does data-handling (ticket content → LLM) need a DPA/region constraint?
4. **Identity model** — confirm the hybrid recommendation (§3).
5. **Test-stack scope** — Java-only first, or polyglot from the start?
6. **Build vs. adopt** — is there appetite to build the orchestration in-house vs. lean on an
   existing agent platform (e.g., Forge remote agents EAP) for the Jira-native parts?

## 9. Immediate next step

Pick the Phase-1 target and identity model, then I scaffold the hosted loop on a new branch
(`feature/qa-platform-phase1`) reusing `JiraClient` + the existing prompts. Everything above
is reversible until we commit Phase 1.
