# Fix: memory writes no longer evict the cached system prompt

## Root cause

`build_system()` in `bot.py` concatenated the static coaching rules
(`INSTRUCTIONS`, ~95% of the prompt) with the per-athlete context — including
the `facts` list that `save_fact` appends to — into a single text block with
one `cache_control` marker. Anthropic's cache key is a hash of the whole
prefix up to a breakpoint, so one appended fact changed the block's hash and
invalidated the entire cached prefix. Every call after a `save_fact` paid a
fresh cache write for the full ~1000 tokens (`cache_creation_input_tokens`
~1000+, `cache_read_input_tokens: 0` in `logs/usage.jsonl`), even though the
fact itself is only ~15 tokens.

## Change

`build_system()` (bot.py:130) now returns two separately marked blocks,
static first:

```python
[
    {"type": "text", "text": INSTRUCTIONS, "cache_control": {"type": "ephemeral"}},
    {"type": "text", "text": athlete_context(a, today), "cache_control": {"type": "ephemeral"}},
]
```

The instructions are a stable first cache segment; the athlete context
(profile, zones, goal, facts, date) is a second, small segment. A `save_fact`
only changes the second segment, so the next call reads the instructions from
cache and re-creates just the ~100-token context block. The marker on the
context block means calls with unchanged context still read it from cache
within the 5-minute TTL. Nothing else changed: tool selection, the tool loop,
and logging are untouched (two of the four allowed breakpoints are used, and
extra breakpoints cost nothing).

## Expected effect on logs/usage.jsonl

After a `save_fact`, round 2 should show `cache_read_input_tokens` at the
instructions size (was 0) and `cache_creation_input_tokens` in the low
hundreds at most (was ~1000+), matching the normal-message pattern. This is
the same shape of fix as "capping facts at 20" attempted to get at, except it
addresses the actual mechanism — eviction of the static prefix — instead of
the fact count.

## Verification (no API calls)

- `build_system()` returns 2 blocks, static block first, both marked.
- Simulated `save_fact`: first block byte-identical before/after; only the
  context block changes; profile edits (goal/zones) still flow through the
  dynamic block as before.
- `reply()` end-to-end with a stub LLM: request plumbing unchanged, no file
  writes. The stub's log line was reverted, so `logs/usage.jsonl` and
  `data/athletes.json` are untouched.

## Caveats

- Sonnet 4.5 requires ≥1024 tokens before a breakpoint; a shorter segment is
  silently not cached (no error). The static block sits just around that
  range, so if the instructions are ever shortened, check the usage fields —
  `cache_creation_input_tokens` and `cache_read_input_tokens` both 0 means
  the segment fell below the minimum.
- `logs/usage.jsonl` also shows full re-creations after messages that add a
  tool group (`plan_week`, `predict_race`), because tool definitions sit
  ahead of the system prompt in the cache prefix. Left as-is per NOTES.md —
  keyword tool filtering is deliberate — but worth knowing the two causes
  apart in the log.
