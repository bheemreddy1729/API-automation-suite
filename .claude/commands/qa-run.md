---
description: Execute the approved tests, show the Allure report, and publish results to a linked Xray Test card
---

# /qa-run

Stage 3 of the QA lifecycle (`/qa-start` → `/qa-approve` → **`/qa-run`**). Run this once
you've verified the generated script(s). Running it means "scripts verified — execute."

## Steps

1. **Execute** (one combined run over the approved classes):
   ```
   mvn test -Dtest=<ClassA,ClassB>
   ```
   Requires `TENANT_201_SECRET` (env var or
   `src/test/resources/config/tenants.properties`). Capture per-method pass/fail and
   expected-vs-actual.

2. **Serve the Allure report (automatic — do not wait to be asked):**
   ```
   mvn allure:serve
   ```
   This generates and opens the report in the browser. It is a **blocking** local web
   server, so run it in the **background**, then read its output for the
   `Server started at <http://...>` line and surface that URL to the user. The server
   stays up until stopped (Ctrl+C, or kill the background task) — tell the user how.
   Static alternative if a server can't bind: `mvn allure:report` →
   `target/site/allure-maven-plugin/index.html`.

3. **Create + link the Xray Test card** (`.claude/prompts/test-card.md` Stages 1-2):
   - `createJiraIssue` → Xray **Test** (project `LBVOICESER`, `issueTypeName: Test`,
     summary `[Automated] <parent summary> — API tests`, description = approved plan).
   - `createIssueLink` type **`Tests`**: `inwardIssue` = new card, `outwardIssue` = parent.
   - Swap `@XrayTest(key=...)` in the Java to the new Test card key.
   - Reuse an existing `Tests`-linked `[Automated]` card if the parent already has one.

4. **Publish results** (`test-card.md` Stage 3):
   - Post a run-summary comment on the **Test card** (counts, per-method result,
     `mvn allure:serve` for the report).
   - **Test card status:** all tests pass → transition the card to **Done** (resolve the
     id via `getTransitionsForJiraIssue`, then `transitionJiraIssue`); any failure → leave
     it **Open** so the red card stays visible.
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
