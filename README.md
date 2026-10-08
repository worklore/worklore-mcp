# worklore-mcp

An MCP (Model Context Protocol) connector for [worklore.dev](https://worklore.dev) —
it lets any MCP-capable agent (Claude, ChatGPT, Cursor, …) search worklore's
developer stories, read one with its **capability disclosure** attached, x-ray any
skill or story before running it — all without an account — and, once you've
signed in, record how a reproduction went, publish a story of your own, or revise
one you published.

- **Endpoint:** `https://worklore.dev/mcp` (Streamable HTTP, JSON-RPC over POST)
- **Auth:** none to search and read public stories. Writes (and your private
  stories) use OAuth 2.1 (PKCE + dynamic client registration). Sign-in is with your
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

Read-only — no sign-in needed (public stories only; `check_capability` with a
`url` needs sign-in, because the server fetches it for you):

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

Since 0.6.0 `resources/list` is a **fixed** list of three documents — the same
for everyone, every day — all readable without an account:

| URI | What it is |
|-----|------------|
| `worklore://guide` | How to use worklore through MCP: search, read a story **with** the user before acting, reproduce it, report honestly (`failed` is useful), x-ray unfamiliar skills and prompts with `check_capability`, publish or edit only with the user's approval |
| `worklore://story-format` | The story format: frontmatter fields, the narrative, the "Reproduce this" contract (prerequisites / your agent will need from you / steps / verify), the optional read-only check, fail stories, proposals, sanitising, the exact-references rule. Read it before drafting a story |
| `worklore://access` | What answers without a token and what needs sign-in — rendered from the one access table the server enforces |

Stories are reached through one **resource template**, `worklore://story/{slug}`
(`resources/templates/list`). Public stories read without a token; a private
story reads only for its author and answers like a missing one to everyone else.
Every `worklore://story/…` URI that `resources/list` handed out before 0.6.0
still reads. To *find* a story, use `search_stories` / `suggest_for_project`.

Why the stories left the list: a list that changes whenever someone publishes
cannot be part of a surface fingerprint — the fingerprint would "break" every day
without anything breaking, and teach clients to ignore a mismatch. The contents
of the three documents may change between releases; the list entries may not
without a new version.

## Verify the surface yourself

A version number is a promise that nothing a client depends on changed without
it. Since 0.6.0 worklore publishes its surface fingerprint in the shared form
**`mcp-surface/1`** ([SPEC](https://github.com/SidneyBissoli/mcp-br-commons/blob/main/packages/mcp-surface/SPEC.md),
by Sidney Bissoli), so you check worklore exactly the way you check every other
server that publishes it. The registry entry carries it in `server.json` under
`_meta` → `io.modelcontextprotocol.registry/publisher-provided` →
`io.github.sidneybissoli/mcp-surface`:

- `declared.sha256` — the sha256 of what a client sees before it calls anything:
  the `initialize` result (protocol version, capabilities, instructions,
  serverInfo without its version) and the four lists (tools, resources, resource
  templates, prompts), normalised and serialised as the SPEC says;
- `anonymous` — which methods answer **without a token** (plus one named,
  harmless `tools/call`: `check_capability` on inline text), and its sha256.

The fastest check is Sidney's dependency-free
[`verify.mjs`](https://github.com/SidneyBissoli/mcp-br-commons/blob/main/packages/mcp-surface/exemplos/verify.mjs)
(Node 18+). It reads the registry entry for the version, makes sure the endpoint
can say "no" to a method that does not exist, captures the live surface, and
compares:

```bash
curl -sO https://raw.githubusercontent.com/SidneyBissoli/mcp-br-commons/main/packages/mcp-surface/exemplos/verify.mjs
node verify.mjs io.github.worklore/worklore 0.6.0
```

Or in Python, with nothing installed (the declared hash only):

```bash
python3 - <<'PY'
import hashlib, json, urllib.request
EP = "https://worklore.dev/mcp"
def rpc(method, params=None):
    body = {"jsonrpc": "2.0", "id": 1, "method": method, **({"params": params} if params else {})}
    req = urllib.request.Request(EP, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"})
    return json.load(urllib.request.urlopen(req)).get("result")
def canon(v):  # SPEC §3: keys by UTF-16 code unit, no whitespace, JSON.stringify strings
    if isinstance(v, dict):
        return "{" + ",".join(json.dumps(k, ensure_ascii=False) + ":" + canon(v[k])
                              for k in sorted(v, key=lambda s: s.encode("utf-16-be"))) + "}"
    if isinstance(v, list):
        return "[" + ",".join(canon(x) for x in v) + "]"
    return json.dumps(v, ensure_ascii=False)
def listed(method, key):  # this server answers each list in one page
    res = rpc(method)
    return res.get(key) if isinstance(res, dict) else None
def by(items, key):
    return None if items is None else sorted(items, key=lambda x: str(x.get(key)).encode("utf-16-be"))
init = rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                          "clientInfo": {"name": "verify", "version": "1"}})
version = init["serverInfo"]["version"]
surface = {"initialize": {"protocolVersion": init.get("protocolVersion"),
                          "capabilities": init.get("capabilities"),
                          "instructions": init.get("instructions"),
                          "serverInfo": {k: v for k, v in init["serverInfo"].items() if k != "version"}},
           "tools": by(listed("tools/list", "tools"), "name"),
           "resources": by(listed("resources/list", "resources"), "uri"),
           "resourceTemplates": by(listed("resources/templates/list", "resourceTemplates"), "uriTemplate"),
           "prompts": by(listed("prompts/list", "prompts"), "name")}
live = hashlib.sha256(canon(surface).encode()).hexdigest()
entry = json.load(urllib.request.urlopen(
    "https://registry.modelcontextprotocol.io/v0.1/servers/io.github.worklore%2Fworklore/versions/" + version))
published = entry["server"]["_meta"]["io.modelcontextprotocol.registry/publisher-provided"][
    "io.github.sidneybissoli/mcp-surface"]["declared"]["sha256"]
print("version", version, "| live", live[:12], "| registry", published[:12],
      "| match" if live == published else "| DIFFERS")
PY
```

If the version is the same and the hash differs, the server changed without
saying so. Tell me in an issue. 0.5.1 published worklore's own per-section
hashes under a `surface` key; 0.6.0 replaced them with this one shared format.
The idea of publishing the fingerprint with each release came from a comment by
[@_firelinks](https://dev.to/_firelinks) under Sidney Bissoli's
[Your MCP server changed. Its version didn't.](https://dev.to/sidneybissoli/your-mcp-server-changed-its-version-didnt-heres-how-to-catch-it-3ai5)

## What answers without a token

Since 0.5.0 one rule decides it, everywhere — the site, the REST API and this
server alike. It lives as a single table in worklore's backend (`access.py`,
rendered as `docs/ACCESS.md`); the summary below is generated from it.

<!-- generated: python3 backend/src/access.py --readme (worklore repo) -->
**The rule.** Anyone can search and read all public stories without signing in — site, REST API and MCP alike. Private stories and every write (publish, edit, report a reproduction or a check, visibility, per-user data, anything acting as a person) need a signed-in session. Anonymous reads go through the single visibility rule, so a private story answers exactly like a missing one. Anything that costs worklore on someone else's behalf — the server fetching an arbitrary URL — needs a session too, unless the input is inline text.

- **Methods with no credential:** `initialize`, `notifications/initialized`, `notifications/cancelled`, `ping`, `tools/list`, `resources/list`, `resources/read`, `resources/templates/list`, `prompts/list`.
- **Tools with no credential:** `search_stories`, `get_story`, `suggest_for_project`, `check_capability` (without `url`) — public stories only; a private story answers exactly like a missing one.
- **Need a signed-in session:** `check_capability` with `url`, `report_reproduction`, `report_check`, `publish_story`, `edit_story`. Without one they answer `401` with a `WWW-Authenticate` header pointing at the authorization server.
- A JSON-RPC batch answers without a token only if every message in it does.
<!-- /generated -->

In practice: you can connect worklore and search, read, get suggestions and
x-ray pasted text without an account. Signing in adds your own private stories
to what you can see, lets `check_capability` fetch a URL for you, and is what
lets your agent record a reproduction or a check, publish, or edit — all of
which act as you.

**History.** Until 0.4.0 the line sat between describing the server and using
it: **the list and the call do not need the same answer.** Anonymous
callers got the server's *description* — names, descriptions, input and output
schemas, annotations — which is the same information already published in the
MCP Registry, in Smithery's listing and in this README. They got nothing that
executed, nothing per-user, and no session. 0.5.0 keeps the last two and opens
reading public stories, which the website never gated in the first place.

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
HTTP). Searching and reading work right away; the first call that needs a session
(a write, or a URL to x-ray) answers `401` and your client is walked through OAuth —
it registers itself, so there is nothing to paste and no API key to manage.

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
