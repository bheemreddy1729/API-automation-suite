# API Automation Suite

REST API test automation in **Java 11 + REST Assured + JUnit 5** (Maven), with
**Jira/Xray** traceability and **Allure** reporting. Built to open directly in an
**Eclipse** workspace.

## What this suite does

1. Runs REST Assured + JUnit 5 tests against a target API (`mvn test`).
2. Connects **Jira Cloud** via the Atlassian (Rovo) MCP server to pull
   requirements / test cases and post run summaries back.
3. Annotates tests with `@Requirement` / `@XrayTest` and imports results into
   **Xray Cloud**, giving a requirement → test → result traceability matrix.
4. Produces **Allure** reports and a coverage / quality / gap evaluation.

## Prerequisites

- JDK 11 (`java -version`)
- Maven 3.9+ (`mvn -version`)
- Node.js 18+ (for the MCP servers) — Node 24 detected
- Eclipse IDE for Java Developers (bundles m2e)

## Project layout

```
pom.xml                                  REST Assured, JUnit5, xray-junit-extensions, Allure
src/test/java/com/laerdal/api/
  config/EnvConfig.java                  env/property resolution (base URI, auth, timeout)
  config/SpecFactory.java                shared RequestSpecification + Allure filter
  clients/                               per-resource API client wrappers (added in Phase C)
  tests/                                 REST Assured + JUnit5 test classes
src/test/resources/
  config/env.properties                  non-secret defaults
  junit-platform.properties              JUnit5 + Xray reporter config
  testdata/                              request payload fixtures
scripts/                                 Xray auth + results import (Phase D)
```

## Configuration

All config resolves in this order (first hit wins):
**JVM `-Dkey=value`  →  OS env var (`UPPER_SNAKE_CASE`)  →  `config/env.properties`  →  built-in default.**

Copy `.env.example` to `.env` and fill it in (the file is git-ignored). Secrets
(tokens, keys) must come from env vars — never `env.properties`.

Defaults target the public `https://jsonplaceholder.typicode.com` demo API so the
suite is green before your real endpoints are wired in.

## Running

```bash
mvn test                 # run all tests
mvn test -Dtest=SmokeTest# run one class
mvn allure:serve         # open the Allure report (after a test run)
```

Override the target at runtime:

```bash
mvn test -Dapi.base.uri=https://api.example.com -Dapi.base.path=/v1 \
         -Dapi.auth.type=bearer -Dapi.auth.token=$env:API_AUTH_TOKEN
```

## Open in Eclipse

This folder is a ready Eclipse project (`.project` / `.classpath` / `.settings`
are committed):

- **Open directly:** File → Open Projects from File System → select this folder.
- **Or import as Maven:** File → Import → Maven → Existing Maven Projects → select
  this folder. (Eclipse's m2e regenerates classpath from `pom.xml`.)

Run tests in Eclipse: right-click `SmokeTest` → Run As → JUnit Test.

If the classpath ever drifts from `pom.xml`, regenerate it:

```bash
mvn -DskipTests eclipse:eclipse
```

## Jira / Xray / Evaluation

See the implementation plan and the per-phase sections:

- **Phase B** — MCP wiring (Atlassian Rovo MCP + an HTTP explorer MCP).
- **Phase C** — pull Jira requirements, explore the live API, generate traced tests.
- **Phase D** — import results to Xray Cloud (`scripts/`), post summary to Jira.
- **Phase E** — Allure report + coverage / gap evaluation.

Reference docs:
- Atlassian Rovo MCP — https://support.atlassian.com/atlassian-rovo-mcp-server/
- Xray import (REST v2) — https://docs.getxray.app/display/XRAYCLOUD/Import+Execution+Results+-+REST+v2
- Xray JUnit 5 extensions — https://github.com/Xray-App/xray-junit-extensions
- Allure + REST Assured — https://allurereport.org/docs/restassured/
