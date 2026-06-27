# Enterprise QA Agent Platform — architecture & roadmap (v1 draft)

> **Status:** planning draft for review. Grounded in the connection experiments on
> branches `feature/jira-rest-connection` (direct REST client) and
> `feature/rovo-mcp-experiment` (proven custom-client MCP consumption).
> **Owner:** Praveen (Laerdal). **Last updated:** 2026-06-27.

## Decision log (updated each cross-review round)

Convergence tracker for the multi-agent deliberation. ✅ decided · 🔄 open/debated ·
🚩 gated on org facts (no amount of AI discussion settles these — only the smoke test +
the SCM/admin/security conversation does).

> **Status: architecture CONVERGED** (rounds 1–10; Claude + Perplexity + Gemini independently
> aligned on the core, adding only refinements/roadmap on top). Remaining 🔄 items resolve when
> the pilot team is picked; 🚩 items need the org. **Next step = execution, not more AI rounds.**

### ✅ Decided
- **Human model:** junior-QA-engineer agent; QA lead is the validator/director. The two
  human gates (plan + script) are kept per team. *(round 1)*
- **Transport = hybrid:** REST + service account for autonomous/headless; **Rovo MCP** for
  interactive/act-as-user. Both proven (REST client built; MCP probe passed). *(round 1)*
- **Delivery = central-but-small is the DEFAULT** (one service, config-onboarding, no team
  runs infra) with **per-tenant credential + execution isolation** inside it. **Per-team
  deployment (Model B) is the documented fallback**, justified only if security vetoes central
  credential custody, or pilot teams are infra-capable and want physical isolation for v1.
  *(round 2 → central; round 3 → **converged (both agents)**: central-but-small default +
  per-tenant isolation contract (§9.1); Model B = security-gated fallback; final scaling call at
  **team #2**, on the security stance + pilot data. Does **not** gate Phase 1.)*
- **Centralize the brain, FEDERATE execution** to each team's existing CI; the platform is
  custodian of **Jira access only**, never teams' codebases/secrets/runtimes. *(round 2)*
- **Identity:** per-team **service accounts** (MVP), least-privilege, in a secret manager,
  with audit + **kill switch**; act-as-user OAuth added later where attribution matters.
- **MVP scope discipline:** approvals in **Jira (no UI yet)**, one pilot team, read-only →
  write-under-QA-lead-approval. Defer web UI / GraphQL API / policy engine.
- **Framing:** design-as-product, implement-as-service, manage-in-repo (lenses, not choices).
- **HITL + versioning** *(round 4, Gemini)*: AI-generated tests **never auto-merge** to critical
  pipelines (human gate stays); **prompts/agents are versioned, auditable artifacts**.
- **Pluggable integration seam** *(round 4)*: design for multiple inbound triggers + outbound
  reporters; **implement one each for MVP** (Jira in, Xray out).
- **MVP I/O pinned** *(round 6, Perplexity)*: inbound trigger = **Jira Automation webhook** on
  "Ready for testing"; outbound reporter = **Xray**. The hybrid MCP/REST split is about
  **identity**, not juggling transports/triggers in Phase 1.
- **Structural isolation enforcement** *(round 6)*: a missing `tenantId` fails at **CI/compile**,
  not runtime; **contract tests** cover both MCP + REST backends; §12 is treated as a **hard
  contract**, not a suggestion.
- **Per-tenant customization = base + config-driven overrides** *(round 7, user's idea)*: layered
  prompts/conventions per tenant via **config, not class inheritance** (tenancy is **data** →
  onboard by config, no per-tenant deploy). Overrides confined to tunable areas; **core
  safety/governance prompts immutable + applied last**; overrides versioned + lead-approved.
  Seam designed in Phase 1, override tooling Phase 2+. (§9.2)
- **Runtime topology** *(round 8)*: **brain** (orchestrate/reason/Jira I/O) is separate from
  **execution** (the team's CI — GitHub Actions — runs the generated tests in the team's env).
  The brain can run **GHA-native for the pilot** (no server → sidesteps the hosting 🚩) and
  graduate to a **central service** at enterprise scale — same code, different host. Doesn't gate
  Phase 1. (§9.3)
- **Model- & framework-agnostic engine** *(round 9, user)*: LLM via a **task-aware model router**
  (coding vs reasoning vs cheap-classify; route by data-sensitivity → in-region). **Corrects the
  earlier "Claude Agent SDK" assumption — no model/vendor is locked.** (§6)
- **Framework-agnostic generation** *(round 9)*: engine generates the **target team's** stack
  (**engine lang ≠ test lang**); pluggable per-stack generators; MVP = Java/JUnit only. (§6, §12)
- **Engine stack = Python + LangGraph** *(round 10, DECIDED)*: model-agnostic via a task-aware
  router (**Azure OpenAI** in-region the lead model candidate; specific model still open). Java
  `JiraClient` is now a proven **reference** + a small Python REST port for the headless path; Rovo
  MCP for interactive. Scaffolding on `feature/qa-platform-phase1`.
- **Test-script language = a plan-start gate input** *(round 10, user)*, **default Python**;
  resolved *explicit choice → per-tenant config → global default (Python)*. Per-stack generators
  pluggable (§6); MVP ships the **Python/pytest** generator. *(Repo location for the engine — its
  own repo vs subdir — is an org-fact for the SCM talk; pilot scaffolds in `engine/` here.)*
- **Proactive PR bug detection** *(round 9)*: roadmap 2nd surface; build-vs-adopt favors Copilot/
  CodeQL unless domain value; triggers the supervisor model. (§7, §12)

### 🔄 Open / debated
- Lead-facing **web UI / GraphQL API** — needed when? (Perplexity earlier; Claude: defer.)
- **Policy engine** — real engine vs simple config guardrails for MVP.
- **Triggers** — scheduler vs Jira Automation webhook vs Slack command vs CI hook for MVP.
- **Test-stack scope** — Java/REST first vs polyglot/UI from the start (UI is roadmap).
- **Reasoning model hosting** — Anthropic API direct vs Bedrock-in-region (ties to compliance).
- **Per-tenant RAG/context engine** *(round 4, Gemini)* — Phase-2 **quality** lever; deferred from
  MVP. ⚠ reintroduces data custody → must obey §9.1 + the compliance 🚩.
- **Agnostic integration adapters** (multi-CI in, Zephyr/Allure out) — roadmap; MVP = Jira + Xray.
- **Supervisor/multi-agent runtime** — Phase 3+ only, *if* the platform serves heterogeneous
  request types. The current phased pipeline is already the needed modularity.

### 🚩 Gated on org facts (SCM / Atlassian admin / security)
- Does **SSO block API-token Basic auth**? *(the `JiraConnectionIT` smoke test answers this.)*
- Can the org **provision per-team service accounts** (+ licensing), or must it be an OAuth
  3LO app?
- Can the org **enable + govern Rovo MCP** (permissions, IP/domain allowlist, audit log)?
- **Hosting** target (Azure / k8s / internal app platform)? *(pilot can run GHA-native, deferring
  this — see §9.3.)*
- **Compliance:** is sending ticket content to the Anthropic API approved? DPA / region pin /
  Bedrock-in-region? What security review gates org-wide rollout?
- Would security **veto a central service** holding write-credentials to many projects?
  (If yes → per-team fallback per §9.)
- **Align to Laerdal's internal AI principles** *(round 4 — Gemini cites "Samaritan AI")*: confirm
  the actual principles exist + get their text, then map platform controls (HITL, audit, data
  handling) to them. Don't assume the specifics. **Deliverable:** a 1-page mapping from each
  control (HITL, audit, data-handling, kill switch, tenant isolation) → each principle, used as
  the reference in security/compliance reviews.

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
| Phase-1 engine scaffold + **structural** tenant isolation | `engine/` (Python + LangGraph); `test_tenant_isolation.py` passes |

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
│   • Model/vendor-agnostic engine; LLM via a task-aware router (§6)    │
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
  Back it with **contract tests** running the same high-level ops (read story, comment, create
  test, transition) against **both** backends, so the MCP and REST paths can't silently diverge —
  the orchestrator picks only an *identity mode*, never "MCP vs REST". *(round 6, Perplexity)*

## 6. The reasoning layer — model- & framework-agnostic

Context-scoring and **test generation** are LLM work (a deterministic service can't generate
tests), but the platform is **not tied to any one model, vendor, or SDK**, and the engine itself
is a separate service (likely **Python**), independent of this Java repo.

**Model-agnostic via a task-aware router.** The engine calls LLMs through a **model router**, not
a hardcoded model. It picks per task:
- **coding models** for test/code generation,
- **reasoning models** for critical decisions (gate calls, spec-vs-behavior judgments),
- **cheap/fast models** for classification (e.g. the context-check verdict),
- and may route by **data-sensitivity** → an **in-region** model for sensitive tenants (ties to
  §9.1 data-handling + the compliance 🚩).

Candidate stack: **Python + LangGraph** (stateful graph orchestration) with models behind a
gateway/router (**Azure OpenAI** in-region a strong compliance fit, or others) — **undecided;
abstraction-first** so the choice isn't locked. MVP = one coding + one reasoning model behind a
simple, config-driven policy; richer routing is roadmap (§12).

**Framework-agnostic generation.** The engine **generates tests in a chosen target stack**
(Python/pytest, Java/JUnit, JS/Playwright, …) and the team's CI runs them (§9.3) — so
**engine language ≠ generated-test language**. The **target test-script language is a plan-start
gate input**, resolved *explicit choice → per-tenant config → global default* (**default Python**,
round 10). Per-stack generators are a pluggable seam; MVP ships the **Python/pytest** generator,
with the pilot's actual stack chosen at the gate (LBVOICESER's existing suite is Java/REST-Assured,
so its tenant config may set Java — or pilot Python/pytest against the API).

> Implication for the connection work: a Python engine reaches Jira via a **Python REST client**
> (headless/service-account path — a small port of the proven `JiraClient` logic) and **Rovo MCP**
> (interactive/act-as-user — already validated from a custom client in `experiments/rovo-mcp`).
> The Java `JiraClient` stays a proven **reference**, not engine code, if the engine is Python.

## 7. Phased roadmap (crawl → walk → run)

- **Phase 1 — Productionize for one team (central service, one tenant).** Host the LBVOICESER
  loop as a service: service-identity REST auth, trigger via scheduler **and/or a Jira
  Automation webhook** on "Ready for testing", human gates intact, **execution federated to the
  team's existing CI**, results to Xray, plus a **kill switch** to disable the agent fast.
  *Goal: the loop runs without Claude Code.*
- **Phase 2 — Multi-project (same team).** Config-driven: onboard a 2nd/3rd project by config,
  not code. Prove the abstraction holds.
- **Phase 3 — Multi-team self-service.** Onboarding portal + admin approval flow; act-as-user
  OAuth; Rovo MCP governance wired in; audit/compliance review.
- **Phase 4 — Polyglot generation** (now a core goal, not "if demanded"): pluggable per-stack
  generators + runners/reporters so non-Java teams onboard. Design the seam early (§6); build per
  stack as teams arrive.
- **Parallel capability (roadmap) — proactive PR bug detection.** A **second product surface**:
  review dev PRs for likely bugs + post inline suggestions. Different trigger (PR opened) and
  output (review comments) → this is the **trigger for the supervisor/multi-agent model** (§12).
  **Build-vs-adopt:** prefer integrating GitHub **Copilot review / Autofix / CodeQL** unless
  **domain-specific** (medical-device) detection adds value they miss. Not MVP.

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
   **Criteria:** *build* if you need cross-team orchestration + federated execution *outside*
   Atlassian and custom QA flows; *adopt* if Forge/Rovo agents natively cover most QA processes.
   Have this answer ready for "why build instead of configure existing tools?".

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

**Recommendation (revised after review): build ONE central service (Model A), but start it
small — central brain + governance, FEDERATED execution.** The earlier "start Model B per-team"
call was wrong: forcing every team to deploy a container + manage secrets kills adoption (you'd
serve only infra-savvy teams) and creates version drift — the opposite of "propagate cleanly."

> **Terminology (avoid a Model A/B mix-up):** an "agent **instance** per team" (§3) is a
> **logical tenant** — scoped by config + credentials *inside* the one shared service — **not** a
> separate container or process. *(clarified round 6, Perplexity)*

Three principles make the central model safe:
1. **Per-team service accounts** + **per-tenant credential & execution isolation** (each
   tenant's token accessed only when acting for that tenant; per-tenant execution boundaries),
   least-privilege scopes, in a secret manager, with audit + a **kill switch**. This — not
   per-team deployment — is how you contain the custody/blast-radius concern. *Caveat:
   multi-tenant isolation must be implemented carefully; per-team deployment gets isolation free
   via physical separation — the main engineering argument for the Model B fallback.*
2. **Execution federates to each team's existing CI.** The agent *triggers* the team's pipeline
   to run tests; the platform never centralizes anyone's source code, secrets, or runtimes. So
   the platform is custodian of **Jira access only**, never of teams' codebases — this is the
   key insight that resolves both the custody and the execution-complexity problems.
3. **"Start small" = small in tenants & scope, not in topology.** One pilot team, read-only →
   write-under-QA-lead-approval, approvals in Jira (no UI yet), one service account. Add teams
   by config; add the vault hardening, act-as-user OAuth, a lead dashboard, and a policy engine
   only as real usage demands.

> Per-team deployment (old Model B) remains a **fallback** only if security vetoes a central
> service holding write-credentials to many projects, or pilot teams are infra-capable and want
> physical isolation for v1. Default to central-but-small.

> **This fork does not gate Phase 1.** One pilot team = one service account = identical code
> under either model; central-vs-per-team only diverges at team #2. So we pick central-but-small
> as the **default direction**, document Model B as the fallback, and make the **final call at
> the multi-team phase** — informed by the security stance (🚩) and real pilot adoption. Building
> the pilot de-risks this more than further debate.

### 9.1 Tenant isolation contract (the artifact for the security conversation)

Choosing central-but-small earns its keep **only if** isolation is enforced structurally, not
by convention. These are the rules to bake into the service from day one and to put in front of
Security so the central model isn't hand-waving — they convert "we'll isolate tenants" into a
checklist Security can audit:

1. **Explicit tenant on every boundary — enforced structurally.** Every external call
   (Jira/MCP/CI) and every secret lookup takes a **required** `tenantId`; a missing one fails at
   **compile/CI**, not just runtime, and a CI check flags any call path lacking it. **No
   ambient / "default tenant" helper, ever** — that omission is the failure mode that leaks
   behavior across teams. *(structural enforcement: round 6, Perplexity)*
2. **Per-tenant credentials.** One service account + one secret per tenant, each with its own
   access policy in the secret manager. **No shared token** across tenants.
3. **Per-tenant execution boundary.** When acting for tenant T, the agent may touch **only** T's
   Jira projects and trigger **only** T's CI, using **only** T's token. Cross-tenant reach is a
   hard failure, logged.
4. **Per-tenant kill switch + global kill switch.** Revoke one tenant's secret and disable its
   flows independently of the others; plus a master off-switch. (Refines the §3 kill switch.)
5. **Per-tenant audit.** Every action tagged with `tenantId` (+ acting identity once act-as-user
   lands); lean on the Rovo MCP audit log as the second control plane.
6. **Per-tenant data-handling.** Ticket content sent to the LLM honors that tenant's config:
   (a) **which projects/issue types** may be sent at all; (b) **redaction rules** (mask patterns
   like patient IDs / PHI before they leave); (c) **region/endpoint** (Anthropic direct vs
   Bedrock-in-region). This is the concrete hook for Laerdal's AI principles + healthcare
   compliance — ties to the 🚩 item. *(specifics: round 6, Perplexity)*
7. **Isolation test.** A standing test proves tenant A's config/token cannot reach tenant B's
   projects — isolation is verified in CI, not asserted in a doc.
8. **Observability (MVP-minimal).** Structured logs carrying `tenantId` + action + result, with
   distinct levels for security events (cross-tenant denial, kill-switch use), plus a one-page
   **runbook** ("disable tenant X fast"; "what to check when a team reports a wrong Jira update").
   Rich per-tenant metrics/dashboards are **Phase 2** — don't gold-plate for one tenant. *(round 6)*

> For the **one-tenant pilot** these mostly reduce to "thread `tenantId` through from the start
> and don't hardcode the team." Cheap now; expensive to retrofit. Building them in is what lets
> Security say yes to central at team #2.

> Concretely: **one repo**, deployed as **one central service** (container + scheduler/webhook),
> serving one pilot team first. That is simultaneously "a repo," "a service," and the seed of "a
> product" — the confusion dissolves once you stop treating them as alternatives.

### 9.2 Per-tenant customization model (base + overrides) — *config, not inheritance*

How does team B's agent differ from team A's? Through a **layered customization model**: a shared
**base** (core prompts, conventions, lifecycle) that each tenant **overlays** with its own
project-specific instructions — domain nuances, coding standards, extra assertions (e.g.
hardware-in-the-loop constraints for a device team; specific API-verification rules for a backend
team).

**Adopt the layering; implement it as config, not class inheritance.** "A base *Master Class* that
tenants subclass/override" is the right *mental model* but the wrong *implementation*:
- Literal per-tenant subclasses put tenant config **in code** → onboarding a team needs a code
  change + deploy, which **breaks the decided "onboard by config, not code"** principle and
  reintroduces drift + release coupling. **Tenancy must be data, not subclasses.**
- Correct pattern: **one immutable engine that composes prompts at runtime** — base template +
  per-tenant overlay fragments merged from config. "Inheritance" = config-merge, not `extends`.

**Guardrails (non-negotiable — doubly so for medical):**
- Overrides are confined to **designated tunable areas** (conventions, stack specifics, extra
  checks). They **cannot** touch core **routing, auth, isolation, or safety/governance**
  instructions (HITL gates, data-handling/redaction, kill switch).
- Core safety/governance prompt sections are **applied last and immutable** — an overlay can *add*
  behavior but cannot *weaken* a gate or a redaction rule. (Stops a careless/malicious override
  from disabling HITL or leaking data.)
- Overrides are **versioned + reviewed** (ties to prompt/agent versioning) and approved by the QA
  lead + platform owner before taking effect.

**Timing:** design the **seam** in Phase 1 (prompts loaded as the one tenant's config/overlay, even
with a single tenant) so it isn't retrofitted; build the multi-tenant override **tooling**
(authoring, review, per-tenant prompt store) in Phase 2+.

### 9.3 Runtime topology — what runs where (the execution boundary)

Federated execution (§9, principle 2) splits the work across **two runtimes**:

| **Central BRAIN** (server *or* a GHA job — see below) | **Team's CI** (GitHub Actions / their CI) |
|---|---|
| Receive trigger (Jira webhook / schedule) | Check out the team's repo |
| Read ticket (Jira/MCP); LLM context-check + test generation | **Run** the generated tests in the team's env (`mvn test …`) with the **team's** secrets |
| Human gates (in Jira); commit/PR the test; **dispatch** the team's workflow | Produce results/Allure artifacts; report back |
| Parse results → update Jira/Xray, transition cards, comment | — |

The brain holds **Jira access only**; the team's CI holds the **code, environment, secrets, and
runtime**. Test execution is decoupled to GitHub Actions exactly as intuited — that *is*
federated execution, and it's why the platform never needs custody of a team's system-under-test.

**Where does the brain itself run? Two options — and the pilot doesn't force the choice:**
- **GHA-native (cheapest pilot):** run the orchestration loop *as* a GitHub Actions workflow
  (Jira webhook → `repository_dispatch`/`workflow_dispatch`). **No server to provision → sidesteps
  the hosting 🚩 for Phase 1.** Ideal for one tenant; weaker as a multi-tenant control plane
  (ephemeral jobs, harder cross-tenant audit/kill-switch).
- **Central service (enterprise target):** a persistent multi-tenant service — the right home for
  cross-tenant governance, audit, kill switch, and always-on webhooks; the §9.1 isolation contract
  is easiest to enforce here.

**Recommendation:** the pilot can run the brain in **GHA** (no infra wait); graduate it to a
**central service** when multi-tenant governance demands it — **same orchestration code, different
invocation host**. Like the central-vs-per-team fork, this **does not gate the Phase-1 scaffold**
(the loop logic is identical; only its trigger/host differs).

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

**Gate (round 9): pick the engine stack before scaffolding** — it sets the scaffold language.
Recommended: **Python + LangGraph**, model-agnostic via a router (**Azure OpenAI** in-region as the
leading model on compliance grounds), Phase-1 generator targeting the pilot's **Java/JUnit** stack,
headless Jira via a small Python port of `JiraClient` (+ Rovo MCP for interactive). *(Earlier this
said "scaffold in Java reusing JiraClient" — superseded: if Python, the scaffold is Python and
`JiraClient` is a reference.)*

Then Phase-1 = the LBVOICESER loop, **one tenant**, brain in **GitHub Actions** (no server yet, §9.3),
`TenantContext`/`tenantId` boundary first (§9.1). The `JiraConnectionIT` smoke test settles the auth
🚩 in parallel. Reversible until we commit Phase 1.

> Credit: the central-service framing, kill-switch, integration recipes (webhook/Slack/CI), and
> policy-engine guardrails were sharpened by a parallel review (Perplexity). The
> federate-execution principle, the MCP↔REST hybrid, and the MVP scope-discipline are this
> doc's additions on top. Round 4 (Gemini) added the pluggable integration seam, per-tenant RAG
> (roadmap), prompt/agent versioning, and AI-principles alignment. Round 6 (Perplexity, final)
> hardened execution: structural isolation enforcement, pinned MVP I/O, data-handling specifics,
> dual-backend contract tests, observability/runbook, and the §12 hard contract.

## 12. Out of scope for MVP (anti-accretion guardrail)

Multi-agent reviews tend to *add* scope. To stay buildable, these are explicitly **deferred**,
each with the trigger that would justify it. None of them changes the Phase-1 pilot.

| Deferred capability | Why not MVP | Trigger to build it |
|---|---|---|
| Supervisor / multi-agent router | The phased pipeline is already modular | Platform serves heterogeneous request types beyond the QA loop |
| RAG / vector-DB context engine | One team's context fits in the prompt; adds data custody + ops | Generation quality needs cross-doc/historical context at scale |
| Multi-CI + multi-reporter adapters | Pilot uses Jira + Xray; seam is enough | A team on a different CI / test-mgmt tool onboards |
| Lead-facing web UI / GraphQL API | Approvals work in Jira | Leads need cross-project dashboards / non-Jira approval UX |
| Full policy engine | Config guardrails + human gates suffice | Rules outgrow config; need dynamic, auditable policy |
| act-as-user OAuth | Service account covers autonomous runs | A flow needs per-user attribution ("done as Alice") |
| Per-tenant override tooling (authoring / review / prompt store) | Pilot has one tenant's prompt set; the §9.2 *seam* is enough | A 2nd team needs its own prompt overlays |
| Polyglot generators (beyond pilot stack) | Pilot team is Java; generate one stack | A non-Java team onboards |
| Rich model-routing policy | MVP = 1 coding + 1 reasoning model, simple rules | Cost/quality tuning across many models/domains needed |
| Proactive PR bug-detection surface | 2nd product; off-the-shelf (Copilot/CodeQL) may cover it | Domain-specific detection generic tools miss + real demand |

> Rule of thumb: **design the seams now (so these slot in), build only the pilot's path.**
>
> Treat this table as a **hard contract** *(round 6, Perplexity)*: every new ask — Slack trigger,
> dashboard, multi-CI — is logged against it and built **only** when its trigger condition is
> actually met, not because it was requested mid-pilot.
