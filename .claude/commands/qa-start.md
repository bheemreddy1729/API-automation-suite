---
description: Start the QA lifecycle — fetch Ready-for-testing tickets, gather requirements, open a test plan for review
---

# /qa-start

Stage 1 of the streamlined QA lifecycle (`/qa-start` → `/qa-approve` → `/qa-run`).
Shared phase detail + constants live in
[ready-for-testing.md](ready-for-testing.md); prompts in `.claude/prompts/`.

Constants: cloudId `86a735d2-77c1-49d1-a610-0f381e05ed90`, project `LBVOICESER`,
trigger status **"Ready for testing"**, skip labels `qa-auto-generated` /
`qa-context-requested`.

## Steps

1. **Fetch** (MCP `searchJiraIssuesUsingJql`):
   ```
   project = LBVOICESER AND status = "Ready for testing" AND issuetype IN (Story, Task)
   AND (labels IS EMPTY OR (labels NOT IN ("qa-auto-generated","qa-context-requested")))
   ORDER BY updated DESC
   ```
   Print the ticket list. If none, stop.

2. **Requirement gathering** (context-check): apply `.claude/prompts/context-check.md`
   to each ticket → SUFFICIENT / INSUFFICIENT. Print a one-line verdict table.

3. **Insufficient path:** for each INSUFFICIENT ticket, apply
   `.claude/prompts/story-update.md` (post the comment to the assignee via
   `addCommentToJiraIssue`), then stamp `qa-context-requested` (`editJiraIssue`).

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
