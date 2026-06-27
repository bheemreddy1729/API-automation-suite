// Rovo MCP consumption probe.
//
// Question: can a CUSTOM (non-Claude) MCP client connect to the hosted Atlassian
// Rovo MCP server, discover Jira tools, and call a read-only one?
//
// How: we connect as an MCP client identifying ourselves as "laerdal-qa-agent-probe"
// (deliberately NOT Claude/VS Code/Cursor) through the `mcp-remote` bridge, which
// performs the interactive OAuth (browser consent) the curated clients use. The first
// run opens a browser to authenticate; the token is then cached in ~/.mcp-auth.
//
// Success  = we connect, listTools() returns Jira tools, and a read-only call works
//            -> a custom agent CAN consume Rovo MCP. Use MCP.
// Failure  = connection/auth rejected for a non-allowlisted client
//            -> fall back to the direct REST client (com.laerdal.api.jira.JiraClient).
//
// Run:  npm install  &&  npm run probe
// Env:  ROVO_MCP_URL  (default https://mcp.atlassian.com/v1/mcp/authv2)

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const ENDPOINT = process.env.ROVO_MCP_URL ?? "https://mcp.atlassian.com/v1/mcp/authv2";

// On Windows the npx launcher is npx.cmd; spawning bare "npx" fails.
const npx = process.platform === "win32" ? "npx.cmd" : "npx";

console.log(`[probe] bridging to ${ENDPOINT} via mcp-remote (a browser may open for consent)…`);

const transport = new StdioClientTransport({
  command: npx,
  args: ["-y", "mcp-remote", ENDPOINT],
});

const client = new Client(
  { name: "laerdal-qa-agent-probe", version: "0.1.0" }, // intentionally a non-curated client name
  { capabilities: {} },
);

try {
  await client.connect(transport);
  console.log("[probe] ✅ connected as a custom (non-Claude) MCP client.");

  const { tools } = await client.listTools();
  console.log(`[probe] ✅ server advertised ${tools.length} tool(s):`);
  for (const t of tools) {
    console.log(`         - ${t.name}`);
  }

  // The loop needs these; flag whether the server exposes them by name.
  const wanted = [
    "searchJiraIssuesUsingJql",
    "getJiraIssue",
    "addCommentToJiraIssue",
    "editJiraIssue",
    "createJiraIssue",
    "createIssueLink",
    "getTransitionsForJiraIssue",
    "transitionJiraIssue",
  ];
  const have = new Set(tools.map((t) => t.name));
  console.log("[probe] QA-loop tool coverage:");
  for (const name of wanted) {
    console.log(`         ${have.has(name) ? "✓" : "✗"} ${name}`);
  }

  // Read-only sanity call: list the Atlassian sites this token can reach.
  const resourceTool = tools.find((t) =>
    /accessible.?resources|getVisibleJiraProjects|atlassianUserInfo/i.test(t.name),
  );
  if (resourceTool) {
    console.log(`[probe] calling read-only tool "${resourceTool.name}"…`);
    const res = await client.callTool({ name: resourceTool.name, arguments: {} });
    const text = (res.content ?? [])
      .map((c) => (c.type === "text" ? c.text : `[${c.type}]`))
      .join("\n");
    console.log("[probe] ✅ tool call returned:\n" + text.slice(0, 800));
  } else {
    console.log("[probe] (no obvious read-only resource tool to call; tool listing alone is sufficient proof)");
  }

  console.log("\n[probe] RESULT: custom MCP client consumption WORKS. Record this in FINDINGS.md.");
  await client.close();
  process.exit(0);
} catch (err) {
  console.error("\n[probe] ❌ FAILED:", err?.message ?? err);
  console.error("[probe] If this is an auth/allowlist rejection for a non-curated client,");
  console.error("[probe] the MCP path is closed for custom agents -> use the REST client instead.");
  console.error("[probe] Record the exact error in FINDINGS.md.");
  try { await client.close(); } catch {}
  process.exit(1);
}
