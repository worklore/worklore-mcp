# worklore-mcp

An MCP (Model Context Protocol) connector for [worklore.dev](https://worklore.dev) —
it lets any MCP-capable agent (Claude, Cursor, …) search worklore's developer
stories, read one with its **capability disclosure** attached, and x-ray any skill
or story before running it.

- **Endpoint:** `https://worklore.dev/mcp` (Streamable HTTP, JSON-RPC over POST)
- **Auth:** none — the v1 tools are read-only over public data
- **Roadmap / progress:** [Project #1](https://github.com/orgs/worklore/projects/1)
  (a "Relay Board" — the human does the site actions, the agent writes the code)

## What it's for

worklore stories are text your agent *executes*. This connector brings them —
and their capability tier — into your agent, so you can find relevant work and
see what it can touch **before** you run it. Tiers describe reach (blast radius),
not virtue, and this is never a "safe" verdict. See the write-up:
[Stop asking "is this skill safe?" — ask "what can it do?"](https://worklore.dev/s/see-what-a-skill-can-do-before-you-run-it-a-stdlib-capabilit)
and the tool it wraps, [skill-xray](https://github.com/worklore/skill-xray).

Capability tiers: **T0** inert · **T1** local · **T2** network · **T3** elevated
(secrets / persistence / privilege) · **T4** opaque (fetches/runs code at runtime).

## Tools

| Tool | Arguments | Returns |
|------|-----------|---------|
| `check_capability` | `text` or `url` | tier (T0–T4) + `sha256` + findings (`file:line`) + endpoints — capability disclosure, read-only |
| `get_story` | `slug` | the story's full markdown (narrative + "Reproduce this" contract) **with** its capability tier + findings |
| `search_stories` | `query` | matching stories (title/summary/tags/stack), each with its capability string |
| `suggest_for_project` | `context` | up to 3 stories worth reproducing here, with why + tier |

All four are annotated read-only. Every result carries a human capability string
(e.g. `T0 · inert — touches nothing`) so a tier code is never shown bare.

## Add the connector

**In Claude Code:**
```
claude mcp add --transport http worklore https://worklore.dev/mcp
```

**On claude.ai (web):** Settings → Connectors → *Add custom connector* → name
`worklore`, URL `https://worklore.dev/mcp`. (Custom connectors need a paid plan.)

**Any other MCP client:** point it at `https://worklore.dev/mcp` (Streamable
HTTP). No credentials required.

## Example prompts

1. *"Use worklore to check what this skill can do before I install it: `<paste a URL or the skill text>`."*
2. *"Search worklore for stories about Flutter golden tests, and tell me each one's capability tier."*
3. *"Here's my project: a Python AWS-Lambda backend with DynamoDB. Suggest 3 worklore stories worth reproducing here, and read me the top one's Reproduce-this contract."*

## Notes

- The connector is a route on worklore's existing backend Lambda; it reuses the
  vendored [skill-xray](https://github.com/worklore/skill-xray) scanner.
- Origin is validated (native clients send none and are allowed; unknown web
  origins are rejected); HTTPS enforced.
- Write tools (publishing / reporting reproductions) are planned for v2 and will
  use worklore's GitHub public-profile sign-in.

MIT-licensed.
