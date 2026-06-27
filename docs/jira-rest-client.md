# Jira REST client — talking to Atlassian without Claude Code / MCP

This is the **connection layer** that lets the QA-loop application speak to Jira on its
own, instead of relying on Claude Code's Atlassian MCP connection.

## Why direct REST (and not MCP)

Atlassian's **hosted** MCP server (`https://mcp.atlassian.com/v1/mcp`) cannot be driven by
a custom backend: you can't register your own OAuth client, dynamic client registration is
unsupported, 3LO credentials are rejected, and redirect URIs are restricted to `localhost`
with a curated client allowlist (Claude, VS Code, Cursor, …). So a standalone app can't do
a normal server-side OAuth integration against it.

The robust, headless alternative is to call the **Jira Cloud REST API v3 directly** with an
API token. No MCP, no browser consent, no admin enablement — runs unattended in CI. That's
what [`com.laerdal.api.jira.JiraClient`](../src/main/java/com/laerdal/api/jira/JiraClient.java)
does. (Decisions confirmed with the user 2026-06-26.)

## Setup

1. **Create an API token** at <https://id.atlassian.com/manage-profile/security/api-tokens>.
2. **Provide credentials via env vars** (never commit them — `.env` is git-ignored):
   ```sh
   set JIRA_EMAIL=you@laerdal.com        # Windows (PowerShell: $env:JIRA_EMAIL="...")
   set JIRA_API_TOKEN=<your-token>
   ```
   Non-secret values (`jira.base.url`, `jira.project.key`, `jira.timeout.ms`) live in
   [`config/env.properties`](../src/test/resources/config/env.properties). Resolution order
   per key: `-Dkey` → `UPPER_SNAKE_CASE` env var → `env.properties` → default — same as
   `EnvConfig`.

## Verify the connection

```sh
mvn test -Dtest=JiraConnectionIT
```

[`JiraConnectionIT`](../src/test/java/com/laerdal/api/jira/JiraConnectionIT.java)
**self-skips** when no credentials are set. With creds it:
- authenticates (`GET /rest/api/3/myself`) and prints the connected user, and
- runs the live **Phase-1 JQL** and prints the matched LBVOICESER tickets — which also
  validates the timestamp-aware fetch (excludes only `qa-auto-generated`, keeps
  `qa-context-requested` for re-evaluation).

## What the client covers

All operations the loop uses (see [ready-for-testing.md](../.claude/commands/ready-for-testing.md)):

| Loop need | `JiraClient` method | Endpoint |
|---|---|---|
| Phase 1 fetch | `searchJql` / `searchAll` | `POST /rest/api/3/search/jql` (token pagination) |
| Read ticket fields | `getIssue` | `GET /rest/api/3/issue/{key}` |
| Insufficient comment | `addComment` | `POST /rest/api/3/issue/{key}/comment` (ADF) |
| Stamp / drop labels | `addLabels` / `removeLabels` | `PUT /rest/api/3/issue/{key}` (`update.labels`) |
| Create Xray Test card | `createIssue` | `POST /rest/api/3/issue` |
| Link Test → parent | `createIssueLink` | `POST /rest/api/3/issueLink` |
| Card transitions | `getTransitions` / `findTransition` / `transition` | `GET`/`POST /rest/api/3/issue/{key}/transitions` |

> Search uses the enhanced `search/jql` endpoint with `nextPageToken`; the legacy
> `/rest/api/3/search` was removed by Atlassian in 2025.

## Notes

- After adding `src/main/java`, regenerate the Eclipse classpath if needed:
  `mvn -DskipTests eclipse:eclipse`.
- This is **step 1** (the connection). The orchestration that currently runs inside Claude
  Code — context-scoring and **test generation** — is LLM work; making the whole loop
  independent means either calling the Claude API from the app or dropping auto-generation.
  That decision is separate from this connection layer.
