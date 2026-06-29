# Removed: the Java/REST-Assured test suite (recovery refs)

When this repo became the **QA Engine** (the brain), the in-repo Java product-test framework was
removed from the working tree. Nothing is lost — git history retains all of it.

## What was removed
- `src/test/java/com/laerdal/api/**` — the TTS REST-Assured + JUnit 5 tests, clients, config
  (`EnvConfig`, `SpecFactory`), model, data, util.
- `src/test/resources/**` — `env.properties`, `junit-platform.properties`, `allure.properties`,
  `testdata/`.
- `pom.xml`, Eclipse project files (`.classpath`, `.project`, `.settings/`), and the root
  `.env.example` (Java-suite oriented).

## Where to find it
- **The full Java suite** is in this repo's history on `feature/qa-platform-phase1`
  (HEAD `878ce76` at strip time) and its ancestors. To inspect or restore a file:
  `git show 878ce76:src/test/java/com/laerdal/api/tests/TtsPostApiTest.java`.
- **The proven Java Jira REST client** (`JiraClient`, `Adf`, `JiraConfig`, `JiraException`) lives on
  `feature/jira-rest-connection` (commit `b8f4998`), under `src/main/java/com/laerdal/api/jira/`.
  It is the **reference for the Python port** (`qa_agent/jira/`).

## Why
The engine generates tests and runs them **federated in each team's own repo/CI** (§9.3); it does
not host a product test suite itself. The proven test conventions and loop logic remain captured in
`.claude/prompts/` + `.claude/commands/`, which the Python nodes reimplement.
