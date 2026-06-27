---
description: Jira-driven QA loop — fetch LBVOICESER tickets ready for testing, generate & run tests, update Jira
---

# /ready-for-testing

> **Streamlined entry points (preferred):** `/qa-start` → `/qa-approve` → `/qa-run`.
> Those three commands drive the lifecycle interactively (plan opens in an editor tab
> for review, then approve, then run). This file is the **shared playbook** they cite —
> the full phase detail, JQL, and constants. Running `/ready-for-testing` directly
> performs the whole flow end-to-end.

Run the AI-driven QA lifecycle loop for **LBVOICESER** (Laerdal TTS / Voice Service).
You orchestrate the phases below. Fetch/context/execute/update are automatic; the plan
and script gates are human approvals — **never run a test without both gates passed**.

Authoritative context: read [docs/application-analysis.md](../../docs/application-analysis.md)
if anything below is ambiguous. Prompt definitions live in `.claude/prompts/`.

## Constants (verified against live Jira 2026-06-26)
- cloudId: `86a735d2-77c1-49d1-a610-0f381e05ed90`  (site `laerdal.atlassian.net`)
- Project: `LBVOICESER`
- Trigger status: **"Ready for testing"**  (NOT "Ready for QA")
- Labels: `qa-auto-generated` = done, **always skipped**. `qa-context-requested` =
  awaiting author; **re-evaluated, not skipped**, once the ticket is edited after the
  request comment (see Phase 2 timestamp gate). One `qa-auto:context-request`-tagged
  comment per ticket; never double-posted.
- Tests live in `src/test/java/com/laerdal/api/tests/`; run with `mvn test`.

---

## Phase 1 — Fetch tickets
Use Atlassian MCP `searchJiraIssuesUsingJql` with:

```
project = LBVOICESER AND status = "Ready for testing" AND issuetype IN (Story, Task)
AND (labels IS EMPTY OR labels NOT IN ("qa-auto-generated"))
ORDER BY updated DESC
```

> Note: requirement tickets in this project are authored as **Story** *or* **Task**
> (e.g. LBVOICESER-1334/1335 are Tasks). Do not narrow this to Story only.
>
> The query intentionally **keeps `qa-context-requested` tickets in the result** (only
> the completed `qa-auto-generated` label is excluded). Those re-entered tickets are
> filtered by the timestamp gate in Phase 2 — JQL alone cannot express "edited after
> the request comment", so that gate lives in the orchestrator.

Fetch fields: `summary, description, status, issuetype, labels, assignee, comment,
updated`. (`updated` and `comment` drive the Phase 2 re-evaluation gate.)
Report the count. If zero, stop and say so.

## Phase 2 — Context check + re-evaluation gate (per ticket)
Classify each fetched ticket first, then evaluate:

**A. Fresh ticket** (no `qa-context-requested` label) — evaluate normally: apply
`.claude/prompts/context-check.md` and collect its `verdict`
(SUFFICIENT / INSUFFICIENT / ERROR) + `detected` / `missing` blocks.

**B. Re-evaluation candidate** (has `qa-context-requested`) — apply the timestamp gate:
1. Find the **latest** comment whose body contains the sentinel `[qa-auto:context-request]`
   and read its `created` timestamp.
   - **No sentinel comment found** (label present but the request comment never landed —
     e.g. a prior post failed): treat as a fresh INSUFFICIENT ticket. Run context-check;
     if INSUFFICIENT it self-heals via Phase 4b (this is the *first* comment, so it is not
     a duplicate).
2. If `fields.updated > <sentinel comment>.created` → the author edited the ticket since
   we asked → **re-run** context-check:
   - **SUFFICIENT** → remove the `qa-context-requested` label (MCP `editJiraIssue`) and
     proceed to Phase 3 (plan) like any sufficient ticket.
   - **INSUFFICIENT** → **stay silent**: keep the label, post **no** comment, skip the
     ticket. (Do not re-comment with the now-different missing fields.)
3. Else (`updated <= <sentinel comment>.created` — untouched since the request) → skip
   silently; no context-check needed.

Print a one-line-per-ticket summary table (mark each row fresh / re-eval→sufficient /
re-eval→still-insufficient / waiting-on-author).

## Phase 3 — Gate 1: test-case plan  (SUFFICIENT tickets only)
For each SUFFICIENT ticket, apply Stage A of `.claude/prompts/test-generation.md` to
produce the test-case table. Present all tables, then ASK the user to
**approve / edit / reject the plan** per ticket:
- **Approve** → proceed to Gate 2.
- **Edit** → the user revises the plan in natural language (add/remove/rename a case,
  change an expected status, adjust which AC a row maps to, etc.). Apply the edits,
  **re-present the revised table**, and ask again. Loop until the user approves or
  rejects. No Java is written until the plan is approved.
- **Reject** → drop the ticket (re-enters queue next sync; not labelled).

## Phase 4 — Gate 2: test script  (approved plans only)
For each approved plan, apply Stage B of `test-generation.md` to write the Java class.
Verify it compiles: `mvn -q test-compile`. Present file path + method table, then ASK
the user to **approve / edit / reject** per ticket.
- **Edit** → the user requests code changes; revise the class, recompile, re-present.
  Loop until approved or rejected.
- **Reject** → delete the generated file(s); ticket NOT labelled; no Test card created.

### Phase 4b — Insufficient path (parallel)
Applies only to **fresh** INSUFFICIENT tickets and the self-heal case from Phase 2-B
(labeled but missing its sentinel comment). A **re-eval candidate that is still
INSUFFICIENT gets nothing here** — it already has its comment + label; stay silent.

For each such ticket, apply `.claude/prompts/story-update.md`. **Write order matters:**
stamp the `qa-context-requested` label first (MCP `editJiraIssue`), then post the
structured comment **last** (MCP `addCommentToJiraIssue`) so the comment is the final
mutation. This keeps `fields.updated ≈ <sentinel comment>.created`, so the Phase 2 gate
(`updated > comment.created`) stays **false** until a human actually edits the ticket —
the bot's own label write never re-triggers a re-eval. The comment must carry the
`[qa-auto:context-request]` sentinel. One comment per ticket per sync; never double-post.
If the comment POST fails, report it and leave the ticket — next sync's Phase 2-B
self-heal (label present, no sentinel comment) re-posts cleanly.

## Phase 5 — Create the Xray Test card + link to parent  (approved scripts only)
Apply `.claude/prompts/test-card.md` (Stages 1-2) for each approved ticket:
- `createJiraIssue` → Xray **Test** issue (`issueTypeName: Test`, project `LBVOICESER`,
  summary `[Automated] <parent summary> — API tests`, description = approved plan).
  Only Project + Summary + Issue Type are mandatory in this project.
- `createIssueLink` type **`Tests`**: `inwardIssue` = new Test card,
  `outwardIssue` = parent ⇒ parent "is tested by" the Test card.
- Set `@XrayTest(key = "<new Test card>")` + `@Requirement({"<parent>"})` in the Java.
- Reuse, don't duplicate: if the parent already has a `Tests` link to an `[Automated]`
  Test card, reuse that card.

## Phase 6 — Execute (human-triggered)
When execution begins, **transition the linked Test card → "In Progress"** (resolve the id
by name via `getTransitionsForJiraIssue`, then `transitionJiraIssue`) so the card reflects
that testing has started. Then do NOT auto-run — tell the user the exact command and wait
for them to run it:
```
mvn test -Dtest=<ClassA,ClassB>        # the approved classes
mvn allure:report                       # or: mvn allure:serve
```
Requires `TENANT_201_SECRET` (env var or `src/test/resources/config/tenants.properties`).
Once the user confirms the run finished, continue to Phase 7.

## Phase 7 — Check Allure + publish results
- Read `target/surefire-reports/` + `target/allure-results/`: total / passed / failed,
  failing method names, expected-vs-actual.
- Apply `test-card.md` Stage 3: post a run-summary comment on the **Test card**
  (counts, per-method result, `mvn allure:serve` for the report).
- Update the **parent**: on all-pass → stamp `qa-auto-generated`; on any failure →
  post a comment @-mentioning the parent's reporter with the failing methods
  (no `qa-auto-generated` label, so it reprocesses after a fix).
- **Transition the Test card by result** (out of "In Progress"; MCP
  `getTransitionsForJiraIssue` to resolve the transition id by name on that card, then
  `transitionJiraIssue`): all tests pass → **Done**; any failure → back to **Open** (so the
  red card is visible until fixed).
- **Do NOT transition the parent** ticket, pass or fail. On all-pass its only change is
  the `qa-auto-generated` label; on failure it stays in "Ready for testing" (unlabelled)
  so it re-queues. (Workflow policy confirmed 2026-06-26.)

Finally, print a **summary report**: tickets processed, Test cards created + linked,
pass/fail counts, comments posted, labels stamped, and the Allure report path.

---

## Decision rules (act on these without asking or consulting the advisor)

Run the flow as a full agent. Pause **only** at the two human gates (Phase 3 plan,
Phase 4 script) and where a rule below or a Hard rule explicitly says **ASK**. The
recurring judgement calls are pre-decided here — apply them directly:

1. **Assert exactly what the AC states; never silently "correct" it.** If an AC looks
   wrong — internally inconsistent, contradicting a sibling ticket, or an obvious
   copy-paste error (e.g. LBVOICESER-1335 expecting 200 where sibling 1330 expects 400) —
   still assert the stated value and add a **Review note / plan flag** describing the
   suspicion. Do not change the assertion to what you think is intended.
2. **A run failure caused by a wrong AC is the assert-as-written rule working, not a
   defect to fix.** Report it neutrally as a *spec-vs-behavior discrepancy*: state
   expected-vs-actual, give **both** readings (the AC needs correcting **or** the endpoint
   is defective), @-mention the parent's reporter, and let them adjudicate. **Never edit
   the test to turn red green.** Leave the parent unlabelled so it re-queues.
3. **Already-implemented tickets:** before planning, check whether a test class already
   exists for the ticket (git status / `tests/`). If so, read it, set it as the plan's
   `Target` class, and surface a **skip / regenerate / extend** choice in the plan's
   Review notes with a stated default (**skip = reuse as-is**). Never silently generate a
   parallel class.
4. **Ticket formatting oddities** (stray backticks, broken markdown, odd spacing): read at
   face value, note the oddity in the plan, and proceed. Not a blocker.
5. **Jira-write authorization is implicit in the command.** Invoking `/qa-run` (or running
   the full loop) is durable authorization for the Jira writes that stage describes —
   Test-card creation, `Tests` links, run-summary comments, and labels. Do not re-ask per
   write. Card creation is **unconditional** (happens regardless of pass/fail); only the
   parent's `qa-auto-generated` label is conditioned on an all-pass result.
6. **Cards: reuse, never speculative, never withheld for red.** One card per parent; reuse
   if already linked. Do not hold card creation just because tests failed — the next cycle
   reuses the same card.
7. **Allure report:** serve it automatically (Phase 7 / `/qa-run` step 2) and surface the
   URL; don't wait to be asked.
8. **Status transitions are rule-driven, not ask-driven** (policy confirmed 2026-06-26):
   Test card lifecycle = created+linked **Open** → **In Progress** when the run starts →
   **Done** on all-pass / back to **Open** on any failure. The **parent is never
   transitioned** (label-only on pass, stays "Ready for testing" on fail). Apply directly.
9. **Timestamp-aware re-evaluation is rule-driven** (Phase 2-B). A `qa-context-requested`
   ticket re-enters the loop *only* when `fields.updated > <sentinel comment>.created`.
   On re-eval: SUFFICIENT → **remove the label** (authorized implicitly, same as rule 5)
   and proceed; still INSUFFICIENT → **stay silent** (keep label, no second comment).
   Never post a duplicate context-request comment; the `[qa-auto:context-request]`
   sentinel is the single source of truth for "already asked". Apply directly.

**Still ASK / don't auto-decide:** the two gates (Phase 3 plan, Phase 4 script); anything a
Hard rule marks ASK.

**Advisor:** optional, and *not* needed for anything covered above. Reserve it for
genuinely novel cases — a ticket shape these rules don't anticipate, two rules in
conflict, or an irreversible action with no rule. Routine flow decisions: just act.

## Hard rules
- Two human gates are mandatory; no test run before both pass.
- Execution is human-triggered (Phase 6) — never auto-run `mvn test`.
- Create exactly ONE Xray Test card per parent feature per run; reuse if one is already
  linked. Created issues cannot be deleted via API — never create speculatively.
- Process each ticket exactly once — the label filter in Phase 1 enforces this.
- Never commit or expose tenant secrets / tokens.
- If the Atlassian MCP is not connected, stop and tell the user to run `/mcp` →
  authenticate `atlassian` first.
