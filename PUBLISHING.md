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
   (name, description, repository, the `remotes` streamable-http URL) **and the
   `_meta` block**: the surface fingerprint (`mcp-surface/1`) is written by
   `python3 scripts/surface_meta.py --write <this repo>/server.json` in the worklore
   repo, from its surface lock; `--check` confirms server.json still publishes it.
   Bump `version` here together with `SERVER_INFO` in the backend.
3. **`mcp-publisher login github`** — opens the GitHub device flow. *(Valentina's
   step — interactive auth; proves ownership of the `io.github.worklore` namespace.)*
4. `mcp-publisher publish`.
5. Verify it resolves via the registry API:
   `curl "https://registry.modelcontextprotocol.io/v0/servers?search=worklore"`.
6. Verify the fingerprint end to end, as any client would:
   `node verify.mjs io.github.worklore/worklore <version>` (Sidney Bissoli's
   [verify.mjs](https://github.com/SidneyBissoli/mcp-br-commons/blob/main/packages/mcp-surface/exemplos/verify.mjs);
   see the README, "Verify the surface yourself"). Publish only AFTER the backend
   serving that version is deployed and `scripts/check_live_mcp_surface.py` is green.

No paid plan needed. This is the cheapest cross-client reach (many clients read
the registry); the Claude / ChatGPT directories are separate, later steps.
