---
description: Execute the approved tests, show the Allure report, and publish results to a linked Xray Test card
---

# /qa-run

Stage 3 of the QA lifecycle (`/qa-start` → `/qa-approve` → **`/qa-run`**). Run this once
you've verified the generated script(s). Running it means "scripts verified — execute."

## Steps

> Test-card lifecycle across this stage: **Open → In Progress (when the run starts) →
> Done (all-pass) / Open (any failure).** The card is created and **linked to the parent**
> before execution so it is visibly *In Progress* while the tests run.

1. **Create + link the Xray Test card, then mark it In Progress**
   (`.claude/prompts/test-card.md` Stages 1-2):
   - `createJiraIssue` → Xray **Test** (project `LBVOICESER`, `issueTypeName: Test`,
     summary `[Automated] <parent summary> — API tests`, description = approved plan).
   - `createIssueLink` type **`Tests`**: `inwardIssue` = new card, `outwardIssue` = parent
     (so the parent shows the linked Test card during the demo).
   - Reuse an existing `Tests`-linked `[Automated]` card if the parent already has one.
   - Swap `@XrayTest(key=...)` in the Java to the Test card key.
   - **Transition the card → In Progress** (resolve the id by name via
     `getTransitionsForJiraIssue`, then `transitionJiraIssue`) to signal execution is
     starting.
   - Reuse detection is by the parent's current `Tests` links: a card that was previously
     **detached** is NOT found, so a fresh card is created (don't re-link stale cards).

2. **Execute** (one combined run over the approved classes):
   ```
   mvn test -Dtest=<ClassA,ClassB>
   ```
   Requires `TENANT_201_SECRET` (env var or
   `src/test/resources/config/tenants.properties`). Capture per-method pass/fail and
   expected-vs-actual.

3. **Serve the Allure report (automatic — do not wait to be asked):**
   ```
   mvn allure:serve
   ```
   This generates and opens the report in the browser. It is a **blocking** local web
   server, so run it in the **background**, then read its output for the
   `Server started at <http://...>` line and surface that URL to the user. The server
   stays up until stopped (Ctrl+C, or kill the background task) — tell the user how.
   Static alternative if a server can't bind: `mvn allure:report` →
   `target/site/allure-maven-plugin/index.html`.

4. **Publish results** (`test-card.md` Stage 3):
   - Post a run-summary comment on the **Test card** (counts, per-method result,
     `mvn allure:serve` for the report).
   - **Test card status (out of In Progress):** all tests pass → transition to **Done**;
     any failure → transition back to **Open** so the red card stays visible
     (resolve ids by name via `getTransitionsForJiraIssue`, then `transitionJiraIssue`).
   - **Parent ticket:** all-pass → stamp `qa-auto-generated`; any failure → comment
     @-mentioning the parent's reporter with the failing methods (leave unlabeled so it
     reprocesses after a fix). **Never transition the parent** (pass or fail) — label only.

5. **Summary report:** tickets executed, Test cards created + linked, pass/fail counts,
   comments posted, labels stamped, Allure report location.

## Rules
- Only run after the script gate; never auto-run from `/qa-start` or `/qa-approve`.
- Created Jira issues cannot be deleted via API — create one Test card per parent,
  reuse if already linked.
- Never expose tenant secrets / tokens in cards or comments.
