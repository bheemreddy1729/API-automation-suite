# Experiment — can a custom agent consume the Atlassian Rovo MCP server?

**Goal:** decide whether the custom QA agent should talk to Jira via **MCP** (Rovo MCP,
tools discovered for free) or via the **direct REST client** we already have
(`com.laerdal.api.jira.JiraClient`).

**The open question (sources conflict):** Atlassian says the hosted Rovo MCP server only
supports a *curated client allowlist* (Claude, VS Code, Cursor, …) and blocks custom
*server-side* OAuth apps — BUT custom clients reportedly connect fine through the
`mcp-remote` localhost-OAuth bridge (the same flow the curated clients use). This
experiment settles it empirically instead of guessing.

## Hypothesis

A custom MCP client (identifying as `laerdal-qa-agent-probe`, *not* Claude) can connect
via `mcp-remote`, list the Jira tools, and call a read-only one. If true, the agent can
consume Rovo MCP and we skip building tool wrappers.

## Prerequisites

- Node ≥ 18 (have: v22) and `npx`.
- An Atlassian account with access to the Jira site, able to complete a **browser
  consent** once. (This step is interactive — it cannot be automated/headless, which is
  itself a finding: MCP here is fine for an attended agent, brittle for CI.)

## Run it

```sh
cd experiments/rovo-mcp
npm install
npm run probe
```

The first run launches `mcp-remote`, which opens a browser for OAuth consent and caches
the token in `~/.mcp-auth`. Subsequent runs reuse the cached token.

Override the endpoint if needed:
```sh
ROVO_MCP_URL=https://mcp.atlassian.com/v1/mcp/authv2 npm run probe
```

## Decision matrix — what each outcome means

| Probe outcome | Conclusion | Next step |
|---|---|---|
| Connects + lists Jira tools + read-only call works | Custom agent **can** consume Rovo MCP | Wire the agent's MCP client to `mcp-remote` (or the Anthropic MCP connector / Agent SDK). No custom Jira tools needed. |
| Connects but **missing** loop tools (see ✓/✗ output) | MCP works but tool surface is incomplete | Use MCP for what it covers, REST (`JiraClient`) for the gaps. |
| Auth/allowlist **rejects** the non-curated client | MCP path closed for custom agents | Use the direct **REST** client; wrap its methods as agent tools. |
| Connects only after manual consent, no refresh for unattended | MCP fine **attended**, not for CI | REST for CI; MCP optional for desktop use. |

## Record results

Write what happened in [`FINDINGS.md`](FINDINGS.md) — the exact tool list, the ✓/✗
coverage, and any error text. That file is the deliverable of this experiment.

> Note: this Node probe is framework-agnostic — it proves *feasibility*. If the agent
> ends up in Java, the same connection is reachable via the MCP Java SDK once feasibility
> is confirmed here.
