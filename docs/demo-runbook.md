# 🎬 DEMO RUNBOOK — Enterprise AI-Powered QA Automation

Paced for ~5 minutes. The live demo is the three-command lifecycle:
`/qa-start` → `/qa-approve` → `/qa-run`. The block diagram is the architecture;
these are the buttons you actually press.

---

## ✅ Pre-demo checklist (do this BEFORE you present)
- [ ] Atlassian MCP connected (`/mcp` → `atlassian` authenticated). **If this is down, the demo can't fetch tickets.**
- [ ] `TENANT_201_SECRET` set (env var or `tenants.properties`) — needed for `/qa-run`.
- [ ] At least one LBVOICESER ticket sitting in **"Ready for testing"** (unlabeled). Confirm it's there.
- [ ] Block diagram open on screen; Claude Code terminal ready.
- [ ] Optional: pre-clear any stale `qa/plans/*.md` so the plan opens fresh.

---

## ⏱️ STAGE 0 — Open (~30 sec) — *point at the diagram*

> **SAY:** "This is our AI-powered QA automation platform. The idea: a Jira requirement goes in, and running, traceable tests come out — but with two human approval gates so AI does the speed and we keep the control. It runs as three commands. Let me show you live."

**DO:** nothing yet — just orient them to the diagram bands top-to-bottom.

---

## ⏱️ STAGE 1 — `/qa-start` (~90 sec) — *Input Sources + Analysis Agent + Gate 1*

> **SAY (before running):** "First command kicks off the engine — it pulls tickets that are *Ready for testing* from Jira, an AI agent reads the requirement, and it drafts a test plan for me."

**▶️ RUN:**
```
/qa-start
```

**While it runs — narrate, pointing at the diagram:**
> **SAY:** "Right now it's hitting **Jira** — the Input Sources band. The **Requirement Analysis Agent** is parsing the ticket: the HTTP method, the endpoint, the acceptance criteria. It decides if there's enough to test — and if a ticket is too vague, it actually comments back on Jira asking the author for detail, instead of guessing."

**⏸️ PAUSE when the plan opens in the editor tab.** This is your key moment.
> **SAY:** "And here's **Gate 1 — Test Case Review.** The AI wrote a plan, but it stops and waits for me. I can edit this table, add review notes, or just approve. The AI never writes code unsupervised."

*(Optionally tweak one line in the plan to show it's real and editable.)*

---

## ⏱️ STAGE 2 — `/qa-approve` (~75 sec) — *Test Generation Agent + Gate 2*

> **SAY:** "I've reviewed the plan. Second command turns that approved plan into actual test code."

**▶️ RUN:**
```
/qa-approve
```

**While it runs:**
> **SAY:** "The **Test Generation Agent** is now writing a real JUnit 5 + REST Assured Java test class — same patterns as our existing suite — and compiling it to prove it's valid."

**⏸️ PAUSE when the Java file opens / compile succeeds.**
> **SAY:** "This is **Gate 2 — Script Review.** Same principle: the code is written and compiled, but nothing runs until I sign off. Two gates, two human checkpoints."

---

## ⏱️ STAGE 3 — `/qa-run` (~90 sec) — *Execution + Reporting + Traceability loop*

> **SAY:** "Script looks good. Final command executes everything."

**▶️ RUN:**
```
/qa-run
```

**While it runs — this is the payoff, point across the bottom bands:**
> **SAY:** "Now the **Execution Agent** runs the tests through Maven. Then watch what happens automatically: it opens the **Allure report**, creates an **Xray Test card** in Jira, links it back to the original story, and posts the results. If everything passes, the card closes as Done. If anything fails, the ticket re-queues and pings the author. So every result is tied straight back to the requirement it came from."

**⏸️ PAUSE when the Allure report opens in the browser.**
> **SAY:** "There's the report — and over in Jira, that story now has a linked, traceable Test card."

---

## ⏱️ STAGE 4 — Close (~20 sec)

> **SAY:** "So that's the full loop: **Jira ticket in, two human gates, tested code and a traceable Xray card out** — AI does the heavy lifting, humans keep the judgment, and nothing loses its link back to the requirement. Happy to dive into any layer."

---

## 🧭 Quick cue card (keep this visible)

| When | Command | Pause to explain |
|---|---|---|
| After intro | `/qa-start` | **Gate 1** — plan opens, you review |
| After reviewing plan | `/qa-approve` | **Gate 2** — code written + compiled |
| After reviewing script | `/qa-run` | Allure report + Xray card appear |

## ⚠️ If something goes sideways
- **No tickets fetched** → say "nothing's queued right now" and walk the diagram instead; or have a backup ticket key ready.
- **MCP not connected** → run `/mcp`, authenticate `atlassian`, retry `/qa-start`.
- **Running long** → skip editing the plan/script; just approve and move on. **Never skip narrating the two gates** — that's the whole trust story.
- **`/qa-run` fails on secret** → that's the execution band; explain it needs `TENANT_201_SECRET` and that the gates/generation already demoed the core value.

---

## Reference — what each command actually does

| Diagram band | What the code actually does | Driven by |
|---|---|---|
| Input Sources | Pulls LBVOICESER tickets in **"Ready for testing"** from Jira via MCP (JQL), skipping the done `qa-auto-generated` label; `qa-context-requested` tickets are re-fetched and re-evaluated once edited since the request comment | `/qa-start` Step 1 |
| Requirement Analysis Agent | Scores each ticket SUFFICIENT / INSUFFICIENT — parses HTTP method, endpoint, ACs from free text; never guesses. Re-eval gate: a `qa-context-requested` ticket is re-checked only when `updated >` its `[qa-auto:context-request]` comment; sufficient → drop label + proceed, still short → stay silent | `context-check.md` |
| (insufficient branch) | Stamps `qa-context-requested`, then posts a structured `[qa-auto:context-request]`-tagged comment to the assignee (label-first, comment-last) | `story-update.md` |
| Test Generation Agent (Stage A) | Builds a test-case plan table, writes it to `qa/plans/<KEY>-plan.md`, opens it in an editor tab | `test-generation.md` Stage A |
| 🚦 Gate 1 — Test Case Review | **You pause.** Edit the plan file / Review notes / chat, then approve | end of `/qa-start` |
| Test Generation Agent (Stage B) | Generates the JUnit 5 + REST Assured Java class, annotates `@Requirement`/`@XrayTest`, compiles with `mvn -q test-compile` | `/qa-approve` |
| 🚦 Gate 2 — Script Review | **You pause.** Verify/edit the script, recompile | end of `/qa-approve` |
| Execution Agent | `mvn test -Dtest=<classes>` | `/qa-run` Step 1 |
| Reporting / Allure | Auto-serves `mvn allure:serve`, surfaces the URL | `/qa-run` Step 2 |
| Xray Test card + traceability | Creates Xray Test card, links `Tests` → parent, swaps in the real `@XrayTest` key | `test-card.md` |
| Publish + feedback loop | Comments results, Test card → **Done** on pass / **Open** on fail; parent gets `qa-auto-generated` on pass or @-mention on fail (re-queues) | `/qa-run` Steps 4-5 |
