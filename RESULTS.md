# worklore MCP — test results

Full test pass for the `/mcp` endpoint (worklore-mcp#18). Re-run: `python3 tests/mcp_test.py`.

Last run: 2026-09-10T14:19Z · endpoint: https://worklore.dev/mcp

```

worklore MCP — full test pass  ·  endpoint: https://worklore.dev/mcp

  ✓ initialize → serverInfo+protocol
  ✓ notifications/initialized → 202, no body
  ✓ ping → empty result
  ✓ tools/list → 4 tools
  ✓ every tool has inputSchema + readOnlyHint
  ✓ unknown method → -32601
  ✓ malformed JSON → 400 / -32700
  ✓ batch → 2 responses (notif omitted)
  ✓ check_capability benign → T0
  ✓ check_capability curl|bash → T4
  ✓ check_capability ~/.ssh → T3
  ✓ check_capability skills-install → T1 (not T3)
  ✓ check_capability url → tier+sha256
  ✓ check_capability no args → -32602
  ✓ check_capability bad url → isError, no crash
  ✓ get_story valid → capability.summary + markdown
  ✓ get_story unknown → -32602
  – get_story hidden/quarantined   [no hidden fixture available]
  ✓ search hits carry capability + about_tiers
  ✓ search no-match → count 0
  ✓ search empty → returns all (>0, capped)
  ✓ search multi-word → AND semantics
  ✓ suggest → ≤3 with capability
  ✓ suggest empty → -32602
  ✓ tools/call unknown tool → -32601
  ✓ no Origin → allowed
  ✓ Origin claude.ai → allowed
  ✓ Origin worklore.dev → allowed
  ✓ Origin evil → 403
  ✓ GET /mcp → 405
  ✓ 6 repeated calls stable

30 passed, 0 failed, 1 skipped
```
