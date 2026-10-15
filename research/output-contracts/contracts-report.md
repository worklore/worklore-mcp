# Output contracts on 525 random registry servers (mcp-drill's method)

Date 2026-10-15. Same random 1,000 from the official MCP registry as rounds 1-2; the 541 that answered `tools/list` anonymously in round 1 were asked again, 525 answered with tools. Read-only: `initialize` + `tools/list` (all pages), never `tools/call`. Tiers computed with mcp-drill's own corruption + validation code (commit ccaee07, `contracts.py`).

| tier | tools | share | share of tools that declare a schema |
|---|---|---|---|
| none | 4720 | 75.6% | – |
| vacuous | 1132 | 18.1% | 74.3% |
| enforceable | 391 | 6.3% | 25.7% |
| total | 6243 | | |

Servers (by their best tool): no schema at all 373 · at most vacuous 73 · at least one enforceable 79 (of 525).

- 73 tools that mcp-drill's code marks enforceable are counted as vacuous here: the corruption builder does not follow `$ref`/`$defs`, so it puts a string where a referenced object belongs and the schema rejects it on `type`, not on a value constraint. Raw mcp-drill tiers: none 4720, vacuous 1059, enforceable 464.
- What rejected the corrupted payload in the enforceable tools (a tool can have several): enum 334, const 95, minimum 58, pattern 40, minItems 8, maxLength 6, exclusiveMinimum 5.
- FastMCP auto-wrapped result schemas (`x-fastmcp-wrap-result`): 23.
- worklore's own server (0.7.0, not in the random sample): 7 of 8 tools vacuous, 1 enforceable.

For comparison, mcp-drill's own study (31 popular servers, mostly stdio, 265 tools): none 56%, vacuous 42%, enforceable 3%.
