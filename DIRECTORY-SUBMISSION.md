# Claude Connectors Directory — submission draft (worklore-mcp#15)

Everything the reviewer needs, ready to paste. Your only manual steps: have a
**Team/Enterprise org** (#14), then submit from the org admin portal and track
feedback. (The MCP Registry, #13, is the free cross-client path and needs no Team plan.)

- **Server name:** worklore
- **Remote MCP URL:** https://worklore.dev/mcp  (Streamable HTTP)
- **Public docs URL:** https://github.com/worklore/worklore-mcp  (README)
- **Privacy policy URL:** https://worklore.dev/privacy.html  (has an "MCP connector" section)
- **Auth:** OAuth 2.1 (PKCE + dynamic client registration); sign-in is GitHub
  public profile only — handle and avatar, no scopes, no email, no repos
- **Tools (8):** `check_capability`, `get_story`, `search_stories`,
  `suggest_for_project` (read-only) and `report_reproduction`, `report_check`,
  `publish_story`, `edit_story` (write, acting as the signed-in user; `edit_story` only on the
  signed-in user's own stories).
- **Tool annotations:** the four read tools are `readOnlyHint: true`;
  `check_capability` is also `openWorldHint: true` (fetches a URL);
  `report_reproduction` and `report_check` are `idempotentHint`; `edit_story` is not idempotent
  (each call appends a revision record). No destructive tools. All eight
  declare an `outputSchema` and return `structuredContent`.
- **Data-handling summary:** read calls use only the arguments the agent sends
  (query / context / slug / text / url) to answer that request; the four write
  tools store what the signed-in author explicitly publishes, revises or reports,
  attributed to their handle — a check result (`report_check`) is kept as one
  latest result per person per story, and only its two counts are public; a revision replaces the story text and appends a
  record (time, kind, note, optional source link), and a correction notifies, inside
  worklore, the people who reported reproducing that story; no email or repository data is requested or stored; `check_capability` may fetch a user-provided URL
  server-side purely to scan it; results are public worklore data + the scanner's
  capability report. HTTPS enforced; Origin validated.
- **Security:** Origin allow-list (native no-Origin clients allowed; unknown web
  origins rejected), HTTPS-only, full test suite in `tests/mcp_test.py`.

### 3 example prompts (exercise different tools)
1. "Use worklore to check what this skill can do before I install it: <URL or text>."
2. "Search worklore for stories about Flutter golden tests, with each one's capability tier."
3. "My project is a Python AWS-Lambda backend with DynamoDB — suggest 3 worklore stories worth reproducing here and read me the top one's Reproduce-this contract."
