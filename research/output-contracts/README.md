# Output contracts on 525 random MCP servers (mcp-drill's check)

Does a tool's `outputSchema` reject a wrong answer? Method from [mcp-drill](https://github.com/TimurRakhmatullin86/mcp-drill) by Timur Rakhmatullin ([his article](https://dev.to/tim860/i-tested-31-mcp-servers-for-contract-compliance-only-3-passed-25gp)): build a result with the schema's structure and types but every value replaced, and validate it. Accepted = vacuous, rejected = enforceable.

- Sample: a seeded random 1,000 from the official MCP registry (2026-10-06, `scan.py`); the 541 that answered `tools/list` without sign-in were asked again on 2026-10-15, 525 answered with tools (6,243 tools).
- Read-only: `initialize` + `tools/list` (all pages). No `tools/call`.
- `contracts.py`: the scan; the corruption + validation functions are copied verbatim from mcp-drill (MIT, commit ccaee07). Needs `jsonschema`.
- `contracts.jsonl`: one row per server with every tool's name, tier and declared `outputSchema`. `round1-results.jsonl`: the 2026-10-06 round the sample comes from.
- `contracts-report.md`: the numbers.

| tier | tools | share |
|---|---|---|
| no outputSchema | 4,720 | 75.6% |
| vacuous | 1,132 | 18.1% |
| enforceable | 391 | 6.3% |

73 tools that mcp-drill's code marks enforceable are counted as vacuous: its corruption builder does not follow `$ref`/`$defs`, so the rejection is a `type` error at the reference, not a value check (see the report).

To rerun: put `round1-results.jsonl` at `random-1000/results.jsonl` next to the scripts, then `python contracts.py`. Server lists change; expect different numbers.
