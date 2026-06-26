---
description: Approve the reviewed test plan(s) and generate the Java test scripts for verification
---

# /qa-approve

Stage 2 of the QA lifecycle (`/qa-start` → **`/qa-approve`** → `/qa-run`). Run this
after reviewing the plan(s) opened by `/qa-start`.

## Steps

1. **Re-read each plan + apply edits.** For every `qa/plans/<KEY>-plan.md`:
   - Read the file back from disk (the user may have edited the table directly or
     added bullets under **Review notes**).
   - Apply those edits AND any changes the user gave in chat to the in-context plan.
   - If the plan changed, briefly show the revised test-case table and update the
     plan file so it matches what will be generated.

2. **Generate the script(s)** with `.claude/prompts/test-generation.md` Stage B:
   - Write the Java class to `src/test/java/com/laerdal/api/tests/<Class>Test.java`,
     following existing patterns (`SpecFactory`, `AuthClient`, `TtsClient`, `EnvConfig`).
   - Annotate `@Feature`, `@Requirement({"<parent>"})`, `@XrayTest(key="<parent>")`
     (placeholder — `/qa-run` swaps in the Test card key), `@DisplayName`.
   - Verify it compiles: `mvn -q test-compile`.
   - Open it in a separate editor tab:  `code "src/test/java/com/laerdal/api/tests/<Class>Test.java"`

3. **Pause for verification.** Tell the user: *verify/edit the script — edit the file
   or tell me changes; I'll re-apply and recompile. When satisfied, run `/qa-run` to
   execute.* (Re-running `/qa-approve` after edits re-applies + recompiles.)

## Rules
- This stage writes local Java only — no Jira writes, no Test card yet (that happens
  in `/qa-run` after execution-time approval).
- Never run `mvn test` here — execution is `/qa-run`.
- If a plan was rejected (user says reject), delete its plan file and skip it.
- One test class per SUFFICIENT ticket; keep the class name stable across re-approvals.
