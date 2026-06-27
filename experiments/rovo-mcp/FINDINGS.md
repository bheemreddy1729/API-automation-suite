# Findings — Rovo MCP consumption probe

**Verdict: a custom (non-Claude) agent CAN consume the Atlassian Rovo MCP server.** ✅

- **Date run:** 2026-06-27
- **Atlassian account / site:** Bheemreddy Praveen Reddy — `laerdal.atlassian.net`
- **Endpoint:** `https://mcp.atlassian.com/v1/mcp/authv2`
- **Probe client name (as seen by the server):** `laerdal-qa-agent-probe (via mcp-remote 0.1.37)` — deliberately non-curated
- **Transport:** StreamableHTTP (mcp-remote `http-first`), MCP protocol `2025-11-25`
- **OAuth server:** `https://auth.atlassian.com/...` discovered automatically by mcp-remote

## Did a custom MCP client connect?

- [x] **Yes** — connected as a non-curated client and completed `initialize` + `tools/list` + `tools/call`.

## Browser consent

- [x] Required once — granted **Read + Search + Write** for `laerdal.atlassian.net`; token cached in `~/.mcp-auth`.
- The OAuth client is **mcp-remote's** (it discovers the auth server and registers); we ride it.
  We do *not* register our own OAuth app — that path is still closed, but routing through
  mcp-remote makes it irrelevant.

## Tools advertised (31)

All 8 QA-loop operations are present:

```
✓ searchJiraIssuesUsingJql   ✓ getJiraIssue            ✓ addCommentToJiraIssue
✓ editJiraIssue              ✓ createJiraIssue         ✓ createIssueLink
✓ getTransitionsForJiraIssue ✓ transitionJiraIssue
```
Plus: getIssueLinkTypes, getVisibleJiraProjects, getJiraProjectIssueTypesMetadata,
getJiraIssueTypeMetaWithFields, lookupJiraAccountId, addWorklogToJiraIssue,
getJiraIssueRemoteIssueLinks, atlassianUserInfo, getAccessibleAtlassianResources,
search, fetch, and 9 Confluence tools.

## Read-only call result

`atlassianUserInfo` →
```json
{"account_id":"712020:0edc3182-...","name":"Bheemreddy Praveen Reddy",
 "email":"bheemreddy.praveen.reddy@laerdal.com","account_status":"active", ...}
```

## Conclusion

- **MCP path is viable** for the custom agent: connect via `mcp-remote`, get all loop tools
  for free (no REST tool-wrapping needed). This is "connect like Claude."
- **Caveat — attended vs CI:** auth needed a one-time **browser consent**. Fine for an agent
  on a workstation; for fully unattended/CI runs the cached token + refresh works for a while
  but isn't a clean service-account model. For headless CI, prefer the direct REST client
  (`com.laerdal.api.jira.JiraClient`).
- **Net recommendation:** attended agent → **Rovo MCP via mcp-remote**; unattended/CI → **REST**.
  Both reach the same Jira; the deciding factor is where the agent runs.
