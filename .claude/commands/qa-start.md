---
description: Start the QA lifecycle — fetch Ready-for-testing tickets, gather requirements, open a test plan for review
---

# /qa-start

Stage 1 of the streamlined QA lifecycle (`/qa-start` → `/qa-approve` → `/qa-run`).
Shared phase detail + constants live in
[ready-for-testing.md](ready-for-testing.md); prompts in `.claude/prompts/`.

Constants: cloudId `86a735d2-77c1-49d1-a610-0f381e05ed90`, project `LBVOICESER`,
trigger status **"Ready for testing"**. Labels: `qa-auto-generated` = done (always
skipped); `qa-context-requested` = awaiting author (re-evaluated when edited since the
request comment — see step 2). Full detail: [ready-for-testing.md](ready-for-testing.md).

## Steps

1. **Fetch** (MCP `searchJiraIssuesUsingJql`):
   ```
   project = LBVOICESER AND status = "Ready for testing" AND issuetype IN (Story, Task)
   AND (labels IS EMPTY OR labels NOT IN ("qa-auto-generated"))
   ORDER BY updated DESC
   ```
   Fetch fields `summary, description, status, issuetype, labels, assignee, comment,
   updated`. The query keeps `qa-context-requested` tickets so step 2 can re-evaluate
   the ones edited since the request. Print the ticket list. If none, stop.

2. **Requirement gathering + re-eval gate** (context-check): see Phase 2 of
   [ready-for-testing.md](ready-for-testing.md). **Fresh** tickets (no
   `qa-context-requested`) → context-check normally. **Re-eval candidates** (labeled
   `qa-context-requested`) → only re-check when `fields.updated > <comment with
   `[qa-auto:context-request]`>.created`; then SUFFICIENT removes the label + proceeds,
   still-INSUFFICIENT stays silent (no second comment). Untouched-since-request → skip.
   Print a one-line verdict table.

3. **Insufficient path** (fresh INSUFFICIENT + self-heal only — never a still-insufficient
   re-eval): apply `.claude/prompts/story-update.md`. Stamp `qa-context-requested`
   (`editJiraIssue`) **first**, then post the sentinel-tagged comment to the assignee via
   `addCommentToJiraIssue` **last** (so `updated ≈ comment.created` and the step-2 gate
   stays false until a human edit). One comment per ticket; never double-post.

4. **Happy path — plan + open a review window:** for each SUFFICIENT ticket:
   - Build the test-case plan with `test-generation.md` Stage A.
   - Write it to `qa/plans/<KEY>-plan.md` using the template below
     (create the `qa/plans/` dir first; it is git-ignored).
   - Open it in a separate editor tab:  `code "qa/plans/<KEY>-plan.md"`

5. **Pause for review.** Tell the user: *review the plan(s) — edit the file directly,
   add lines under "Review notes", or tell me changes in chat — then run
   `/qa-approve` to approve and generate the scripts.* Do not generate Java yet.

### Plan file template (`qa/plans/<KEY>-plan.md`)
```markdown
# Test Plan — <KEY>  (<summary>)

> Review: edit the table, add bullets under "Review notes", or tell me in chat.
> Then run /qa-approve. Nothing is generated until you approve.

## Detected
- Method: <METHOD>
- Endpoint: <PATH>
- Acceptance criteria:
  1. ...

## Test cases
| # | method | maps to | expected |
|---|--------|---------|----------|
| 1 | <name> | AC1     | <status> |

## Target
- Class: com.laerdal.api.tests.<Class>Test
- Parent ticket: <KEY>

## Review notes (add edit requests here)
-
```

## Rules
- Read-only on Jira except the insufficient comment + label.
- Open exactly one plan file per SUFFICIENT ticket; keep the agent's in-context copy
  in sync with what was written.
- If the Atlassian MCP is not connected, stop and tell the user to run `/mcp`.
