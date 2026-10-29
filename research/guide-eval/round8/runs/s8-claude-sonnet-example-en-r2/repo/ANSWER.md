# Cache fix: memory writes no longer evict the static instructions

## Cause
`build_system` (bot.py) put `INSTRUCTIONS` + athlete context (date, profile, zones, goal, facts)
into ONE block with ONE `cache_control` marker. Prompt caching is a prefix hash, so `save_fact`
changing the facts changed the hash of the whole block. The next call showed
`cache_read_input_tokens: 0` and `cache_creation_input_tokens` ~1000 in `logs/usage.jsonl`.

## Change
`build_system` now returns two text blocks, each with `cache_control: ephemeral`:
1. `INSTRUCTIONS`: static, byte-identical for every user and day (checked: no interpolation).
2. `athlete_context(...)`: the volatile tail (date, profile, zones, goal, facts, language).

A memory write now invalidates only the tail. Nothing else changed: tool filtering is untouched
(NOTES.md says to leave it), and I did not add top-N fact selection, since per-message selection
would make the tail miss every time.

## Colleague's note: what applied
- Applied: the two-marker split, the byte-stability rule, "load all facts, don't select", and
  checking `usage` afterwards.
- Applied as a caveat: tools sit above the system prompt in the prefix, so a message that adds a
  tool group (plan/race keywords) changes the prefix and re-caches everything once.
- Not applicable: the ~55 tools and the MCP setup. This bot has 4 tools, and the token sizes
  (780 / 240) are theirs, not ours.

## Risk I could not test (no API access here)
Sonnet 4.5 only caches prefixes of at least 1024 tokens. From the log, the full prompt is ~1050
tokens and the tail is ~100-250. That puts the static part (core tools + instructions) at roughly
800-950 tokens, which may be BELOW the minimum. If so, the first marker creates no cache entry on
its own. The second marker still caches the whole prompt, so behaviour would be no worse than
before, but a memory write would still miss.

After deploying, check with the Verify steps from the note. Send two messages, then trigger a
`save_fact`, then send a third. If the third call has `cache_creation` of the full prompt size,
the static prefix is under the minimum. Then either always send all tools (this adds ~150 tokens,
makes the tools array stable, and takes the prefix over 1024; it costs little with only 4 tools but
reverses the keyword filtering), or accept the current behaviour. I did not make that call
because NOTES.md says to keep the filtering.
