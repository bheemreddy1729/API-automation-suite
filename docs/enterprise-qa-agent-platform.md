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

> **Clarify the "assume any identity" instinct.** You don't want *one* agent that impersonates
> arbitrary people across every project — that's an impersonation/audit problem and a huge blast
> radius. Mirror the human: a junior QA engineer has **one** account scoped to **their** team's
> projects. So each team's agent runs as a **team-scoped identity** — a dedicated "Team X QA bot"
> service account, or act-as-user OAuth for that team's members — never a universal impersonator.
> "Broader Atlassian" (Confluence, etc.) rides the same identity; the Rovo MCP already exposes
> those tools.

### The human model we're automating

| Human | Agent equivalent |
|---|---|
| Junior QA engineer (embedded in one team) | One agent **instance per team**, scoped to that team's projects + conventions |
| Understands features, to-and-fro with dev | Reads tickets/ACs (+ comments) ; posts context-requests; reads replies |
| Drafts test plan, **gets QA-lead approval** | Generates the plan ; **human gate = the QA lead approves/edits/rejects** |
| Executes tests, updates the Jira Test card | Runs the suite, writes results + transitions the card (traceability via Xray) |
| Reciprocates with dev + lead | Comments back, @-mentions, summary report |

The QA **lead stays in the loop as the validator/director** — that's the existing two-gate
design, kept per team. UI/path-based testing is the *same loop with a different runner*
(Playwright/Selenium instead of REST-Assured) — roadmap, not MVP; the identity/delivery
architecture below does **not** change for it.

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

## 9. Delivery model — repo, service, or product? (resolving the confusion)

These are **three lenses, not three choices** — you end up with all three:
- **Repo** = where the code lives (always).
- **Service** = a hosted runtime (a *deployment* choice).
- **Product** = how teams discover, onboard, and get support (the org-facing wrapper).

The real fork is **how it runs per team**:

| | **Model A — Central multi-tenant service** | **Model B — Per-team packaged deployment** |
|---|---|---|
| Shape | One hosted platform; teams onboard by config | One repo ships a container/template each team runs |
| Identity | Central **vault** holds many teams'/users' creds; service assumes the right one | Each team uses **its own** team identity; no central vault |
| Pros | Max governance, central updates & visibility | Isolation by construction; team owns secrets; ship-versions-they-adopt |
| Cons | **You** become custodian of org-wide Jira creds — large security/compliance surface; 24/7 ops | Drift across teams; harder to push updates centrally |

**Recommendation: start Model B → graduate the proven path to Model A.** Begin with a
per-team packaged deployment where each team runs the agent under its own scoped identity;
once adoption and governance demand central visibility, promote the popular path into a
managed central service. Rationale: it matches the human analogy (a junior embedded in **one**
team with **one** scoped identity), and it defers the hardest problems — central credential
custody, multi-tenant auth, always-on ops, and the compliance of a shared credential vault —
until you've earned the right to take them on. For a medical-device org, *not* being the
day-one custodian of everyone's Jira tokens is a feature.

> Concretely for Phase 1: **one repo**, packaged as a **container + scheduled job** a team runs
> with **its own service identity**. That is simultaneously "a repo," "a service," and the seed
> of "a product" — the confusion dissolves once you stop treating them as alternatives.

## 10. What to ask in the SCM / platform discussion

> Bring the right people: **SCM/DevOps** (repo, CI, hosting), the **Atlassian org admin**
> (identity, Rovo MCP governance), and **IT security/compliance** (data handling). Several
> asks below are for the admin/security folks, not SCM — flag that when you book it.

**A. Source control & CI/CD**
- Where does the repo live (org GitHub/Bitbucket) and what's the access model?
- Can CI hold **per-team secrets** securely (scoped, not shared)? Which runners?
- If teams consume a shared container/template, what's the **versioning/release** model?

**B. Atlassian administration** *(org admin)*
- Can we provision **per-team service accounts** for the QA bot? Licensing impact?
- If not, can we register an **OAuth 2.0 (3LO) app** (org-approved) for act-as-user?
- Is **API-token Basic auth** permitted, or disabled by SSO policy? *(the `JiraConnectionIT`
  smoke test answers this empirically — run it early.)*
- Can the org **enable + govern the Rovo MCP server** — permissions tab, domain/IP allowlist,
  audit log? Who administers it?
- What **Jira permission granularity** can the bot identity get (ideally project-scoped)?

**C. Identity & secrets**
- Where do credentials live — **Key Vault / secrets manager**? Per-team scoping + **rotation**?
- Who owns the credential lifecycle?

**D. Hosting / runtime**
- Approved hosting for an **always-on service or scheduled job** (Azure / container platform / k8s)?
- Is **outbound egress to the Anthropic API** (and Atlassian) allowed from that environment?
- **IP allowlist** coordination — Atlassian requires requests from allowlisted IPs.

**E. Security & compliance** *(medical)*
- **Data handling:** ticket content (descriptions, ACs, comments) is sent to the **Anthropic API**.
  Approved? Need a DPA, region pinning, or Bedrock-in-region instead of the direct API?
- Required **security review / threat model / pen-test** before org-wide rollout?
- Audit & traceability expectations.

**F. Ownership & support**
- Who **owns** the platform long-term? On-call / SLAs?
- How do teams **request onboarding** and support?

## 11. Immediate next step

Pick the Phase-1 target and identity model, then I scaffold the hosted loop on a new branch
(`feature/qa-platform-phase1`) reusing `JiraClient` + the existing prompts — packaged per §9
(container + scheduled job, team-scoped identity). Everything above is reversible until we
commit Phase 1.
