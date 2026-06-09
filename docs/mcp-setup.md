# MCP Setup (Phase B)

This project ships a project-scoped [`.mcp.json`](../.mcp.json) with two MCP servers:

| Server | Transport | Purpose |
|--------|-----------|---------|
| `atlassian` | Remote HTTP (`https://mcp.atlassian.com/v1/mcp/authv2`) | Read Jira requirements / Xray Test issues, post run summaries back |
| `http-explorer` | Local stdio (`npx @tokenizin/mcp-npx-fetch`) | Probe the live (spec-less) API to discover responses while drafting tests |

When you open this project in Claude Code, you'll be prompted to **approve the
project MCP servers** (because they come from `.mcp.json`). Approve them.

## 1. Atlassian (Jira Cloud)

The endpoint supports both auth methods. Pick one:

### Option A — OAuth 2.1 (default, no admin toggle needed)
1. In Claude Code, run `/mcp`.
2. Select **atlassian → Authenticate**. A browser opens for Atlassian login + consent.
3. The first user to authorize must have access to the relevant Jira project.

> OAuth sessions can drop mid-session on long runs. If that's disruptive, use API tokens (Option B).

### Option B — API token (stable for CLI/automation; requires admin enablement)
1. Your **org admin** must enable API-token auth in the Atlassian Rovo MCP server settings.
2. Create a token at <https://id.atlassian.com/manage-profile/security/api-tokens>.
3. Provide it as a Basic Auth header. Set the values in your environment (see `.env.example`:
   `JIRA_EMAIL`, `JIRA_API_TOKEN`) and configure the header per Atlassian's client docs.

Reference: <https://support.atlassian.com/atlassian-rovo-mcp-server/docs/setting-up-clients/>

### Verify
- `claude mcp list` shows `atlassian` connected.
- Ask Claude to "list issues in project `<YOUR_KEY>`" — it should return real issues.

## 2. http-explorer (live API)

No credentials needed to install. It fetches URLs (JSON/HTML/text) with optional
custom headers, so Claude can GET your endpoints and inspect real responses while
writing tests.

- For **authenticated** requests, pass your API's auth header when invoking the tool.
- For **POST/PUT/DELETE** exploration with bodies, we use `curl` or a throwaway REST
  Assured call during Phase C (this fetch server is GET-oriented).

### Verify
- `claude mcp list` shows `http-explorer` connected.
- Ask Claude to fetch `https://jsonplaceholder.typicode.com/posts/1` — it returns the JSON.

## Notes
- `.mcp.json` contains **no secrets** — only URLs/commands. Tokens stay in env vars / `.env`.
- The old SSE endpoint `https://mcp.atlassian.com/v1/sse` is retired after **2026-06-30**;
  this project already uses the `/v1/mcp/authv2` endpoint.
