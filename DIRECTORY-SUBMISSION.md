# Claude Connectors Directory — submission draft (worklore-mcp#15)

Everything the reviewer needs, ready to paste. Your only manual steps: have a
**Team/Enterprise org** (#14), then submit from the org admin portal and track
feedback. (The MCP Registry, #13, is the free cross-client path and needs no Team plan.)

- **Server name:** worklore
- **Remote MCP URL:** https://worklore.dev/mcp  (Streamable HTTP)
- **Public docs URL:** https://github.com/worklore/worklore-mcp  (README)
- **Privacy policy URL:** https://worklore.dev/privacy.html  (has an "MCP connector" section)
- **Auth:** none (v1 tools are read-only over public data)
- **Tool annotations:** all 4 tools are `readOnlyHint: true`; `check_capability`
  also `openWorldHint: true` (fetches a URL). No destructive tools in v1.
- **Data-handling summary:** read-only tools; each call uses only the arguments
  the agent sends (query / context / slug / text / url) to answer that request;
  no per-user profile is stored; `check_capability` may fetch a user-provided URL
  server-side purely to scan it; results are public worklore data + the scanner's
  capability report. HTTPS enforced; Origin validated.
- **Security:** Origin allow-list (native no-Origin clients allowed; unknown web
  origins rejected), HTTPS-only, full test suite in `tests/mcp_test.py` (30/30).

### 3 example prompts (exercise different tools)
1. "Use worklore to check what this skill can do before I install it: <URL or text>."
2. "Search worklore for stories about Flutter golden tests, with each one's capability tier."
3. "My project is a Python AWS-Lambda backend with DynamoDB — suggest 3 worklore stories worth reproducing here and read me the top one's Reproduce-this contract."
