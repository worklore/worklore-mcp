# worklore-mcp

An MCP (Model Context Protocol) connector for [worklore.dev](https://worklore.dev) —
it lets any MCP-capable agent (Claude, ChatGPT, Cursor, …) search worklore's
developer stories, read one with its **capability disclosure** attached, x-ray any
skill or story before running it, and — once you've signed in — record how a
reproduction went, publish a story of your own, or revise one you published.

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
| `report_check` | `slug`, `result` (`has_problem`/`no_problem`), `note` *(optional)* | the recorded result of a story's read-only "Check if this applies to you" section, run in your project. Only for stories that have one (`get_story` says `has_check: true`). **Never record "not applicable"** — when your project does not match the check's preconditions, don't call it. One result per person per story; the latest replaces the earlier one |
| `publish_story` | `markdown`, or the parts (`title`, `narrative`, `reproduce`, `tags`, `type`, `stack`) | the published story's slug + URL. **Only ever call this with the author's explicit approval of the full draft** |
| `edit_story` | `slug`, `markdown` (the full revised story), `kind` (`rephrase`/`addition`/`correction`, default `rephrase`), `note` *(required for a correction)*, `source` *(optional https URL)* | the slug, URL, the recorded `revision` (`at`, `kind`, `note`, `source`) and how many reproducers were `notified`. Only the story's author can edit it. **Show the author a before/after diff and get their approval first.** The story's `date` never changes. If something in the story was wrong, it is a `correction` — which tells everyone who reproduced it — never a rephrase |

All eight carry MCP annotations (`readOnlyHint` / `openWorldHint` / `idempotentHint`)
so a client can tell the user what a call will do before they approve it, and all
eight declare an `outputSchema` and return `structuredContent`, so a consuming agent
can rely on shape instead of parsing prose.

Every result carries a human capability string (e.g. `T0 · inert — touches
nothing`) so a tier code is never shown bare.

## Resources

Published stories are also exposed as MCP **resources** under `worklore://story/`,
paginated, so a client that browses resources sees the library without calling a
tool. To *find* a specific story, use `search_stories` / `suggest_for_project`
rather than walking every page.

## What answers without a token

Six methods answer with no credential at all — `initialize`, `ping`,
`notifications/initialized`, **`tools/list`**, and (since 0.4.0)
**`resources/list`** and **`resources/read`**. Resources go through the same
visibility rule as the site: without a token you get public stories only; with
one, public stories plus your own private ones; a private story read anonymously
answers exactly as a missing one. `tools/call` still needs a session and returns
`401` with a `WWW-Authenticate` pointing at the authorization server.

The rule is: **the list and the call do not need the same answer.** Anonymous
callers get the server's *description* — names, descriptions, input and output
schemas, annotations — which is the same information already published in the
MCP Registry, in Smithery's listing and in this README. They get nothing that
executes, nothing per-user, and no session.

This is written down because it was a mistake first. The original build gated
the whole endpoint, on reasoning that felt airtight: one gate, one place to get
it right. The consequence was invisible from inside the code and obvious from
outside — a registry-mirroring directory listed worklore with its name, its
description, and **zero tools**, because a crawler has nobody to authenticate
as. The same property also means nobody outside the repository — a scanner, a
conformance harness, a curious stranger — can check what the server actually
publishes. Two symptoms, one cause. The fix was about fifteen lines: an
allow-list of anonymous methods plus a batch check, so a privileged call cannot
be smuggled in beside an anonymous one.

The whole thing is written up, with the diff and how to verify it against your
own endpoint, here: [**My MCP server hid its own tool list behind a
login**](https://worklore.dev/s/2026-09-27-my-mcp-server-hid-its-own-tool-list-behind-a-login).
If somebody proposes gating enumeration on a server you work on, that page is
the short version of the argument.

Gating enumeration is a legitimate choice for a server whose tool *names* are
sensitive. It is worth making on purpose rather than inheriting it from a
transport-level gate, which is how most of them happen — including, by their
own audit, the one that prompted this section being written down.

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
