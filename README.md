# worklore-mcp

An MCP (Model Context Protocol) connector for [worklore.dev](https://worklore.dev) —
it lets any MCP-capable agent (Claude, ChatGPT, Cursor, …) search worklore's
developer stories, read one with its **capability disclosure** attached, x-ray any
skill or story before running it, and — once you've signed in — record how a
reproduction went or publish a story of your own.

- **Endpoint:** `https://worklore.dev/mcp` (Streamable HTTP, JSON-RPC over POST)
- **Auth:** OAuth 2.1 (PKCE + dynamic client registration). Sign-in is with your
  GitHub **public profile** only — worklore sees your handle and avatar, no
  scopes, no email, no repositories.
- **Listed on:** the [official MCP Registry](https://registry.modelcontextprotocol.io)
  as `io.github.worklore/worklore`, and [Smithery](https://smithery.ai/servers/worklore/worklore)
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

Read-only — no sign-in needed beyond connecting:

| Tool | Arguments | Returns |
|------|-----------|---------|
| `check_capability` | `text` or `url` | tier (T0–T4) + `sha256` + findings (`file:line`) + endpoints, plus behavioral red flags — capability disclosure |
| `get_story` | `slug` | the story's full markdown (narrative + "Reproduce this" contract) **with** its capability tier + findings |
| `search_stories` | `query` *(optional)* | matching stories (title/summary/tags/stack), each with its capability string |
| `suggest_for_project` | `context` | up to 3 stories worth reproducing here, with why + tier |

Write — these act as **you**, and need your authenticated session:

| Tool | Arguments | Returns |
|------|-----------|---------|
| `report_reproduction` | `slug`, `result` (`worked`/`partial`/`failed`), `note` *(optional)* | the recorded reproduction. `failed` is a useful report and must never be inflated |
| `publish_story` | `markdown`, or the parts (`title`, `narrative`, `reproduce`, `tags`, `type`, `stack`) | the published story's slug + URL. **Only ever call this with the author's explicit approval of the full draft** |

All six carry MCP annotations (`readOnlyHint` / `openWorldHint` / `idempotentHint`)
so a client can tell the user what a call will do before they approve it, and all
six declare an `outputSchema` and return `structuredContent`, so a consuming agent
can rely on shape instead of parsing prose.

Every result carries a human capability string (e.g. `T0 · inert — touches
nothing`) so a tier code is never shown bare.

## Resources

Published stories are also exposed as MCP **resources** under `worklore://story/`,
paginated, so a client that browses resources sees the library without calling a
tool. To *find* a specific story, use `search_stories` / `suggest_for_project`
rather than walking every page.

## Add the connector

**In Claude Code:**
```
claude mcp add --transport http worklore https://worklore.dev/mcp
```

**On claude.ai (web):** Settings → Connectors → *Add custom connector* → name
`worklore`, URL `https://worklore.dev/mcp`. (Custom connectors need a paid plan.)

**Via Smithery:**
```
npx -y smithery mcp add worklore/worklore
```

**Any other MCP client:** point it at `https://worklore.dev/mcp` (Streamable
HTTP). Your client will be walked through OAuth on first connect — it registers
itself, so there is nothing to paste and no API key to manage.

## Example prompts

1. *"Use worklore to check what this skill can do before I install it: `<paste a URL or the skill text>`."*
2. *"Search worklore for stories about Flutter golden tests, and tell me each one's capability tier."*
3. *"Here's my project: a Python AWS-Lambda backend with DynamoDB. Suggest 3 worklore stories worth reproducing here, and read me the top one's Reproduce-this contract."*

## Notes

- The connector is a route on worklore's existing backend Lambda; it reuses the
  vendored [skill-xray](https://github.com/worklore/skill-xray) scanner.
- Origin is validated (native clients send none and are allowed; unknown web
  origins are rejected); HTTPS enforced.
- How this server was built and shipped, end to end, including what went wrong:
  [Build and ship your own MCP server](https://worklore.dev/paths/build-and-ship-your-own-mcp-server).

MIT-licensed.
