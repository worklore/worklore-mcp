# Publishing to the Official MCP Registry (worklore-mcp#13)

The server is a remote MCP over `https://worklore.dev/mcp`. The registry verifies
ownership of the `io.github.worklore/*` namespace via a GitHub login, so the
`login` step is interactive and must be run by a worklore org member.

## Prep (done)
- `server.json` in this repo holds the values (name, description, remote URL).

## Steps
1. Install the publisher CLI (see https://modelcontextprotocol.io/registry/quickstart),
   then from this repo:
2. `mcp-publisher init` — regenerates `server.json` against the CURRENT schema;
   re-apply the values from the committed `server.json` if it overwrites them
   (name, description, repository, the `remotes` streamable-http URL).
3. **`mcp-publisher login github`** — opens the GitHub device flow. *(Valentina's
   step — interactive auth; proves ownership of the `io.github.worklore` namespace.)*
4. `mcp-publisher publish`.
5. Verify it resolves via the registry API:
   `curl "https://registry.modelcontextprotocol.io/v0/servers?search=worklore"`.

No paid plan needed. This is the cheapest cross-client reach (many clients read
the registry); the Claude / ChatGPT directories are separate, later steps.
