# Fix: memory writes no longer evict the cached system prompt

## Root cause

`build_system()` in `bot.py` concatenated the static coaching instructions
(`INSTRUCTIONS`, ~1000 tokens) and the volatile per-athlete context (profile,
zones, goal, and the growing `facts` list) into a **single** text block with
one `cache_control` marker. Anthropic's prompt cache matches whole prefixes, so
when `save_fact` appended a fact, the very next API call (round 2 of the same
message, plus every call until the next change) saw a different block, missed
the cache entirely, and paid cache-creation price for the full prompt again.
That is exactly the pattern in `logs/usage.jsonl`: every call right after a
`save_fact` shows `cache_read_input_tokens: 0` and
`cache_creation_input_tokens` back up at ~1000+.

## Change

Split the system prompt into two cache blocks in `build_system()`
(`bot.py:130`):

1. Block 1 — `INSTRUCTIONS` (never changes) with a `cache_control` marker.
2. Block 2 — `athlete_context(a, today)` (changes only when a fact is written),
   also with a `cache_control` marker.

The static block comes first, so a memory write only invalidates the small
(~200-token) athlete block; the instructions are served from the existing cache
entry at cache-read price. The athlete block is still marked, so messages that
don't write a fact continue to read both blocks from cache within the
5-minute window.

Also updated the caching sentence in `README.md` to describe the two-block
behavior.

## Result

After a `save_fact`, the next call re-creates ~215 tokens of athlete context
instead of ~1061 tokens of full prompt — the instructions stay cached.

## Verification

No network calls (fake LLM, temp data paths inside the working directory,
cleaned up afterwards):

- `python3 -m py_compile bot.py`
- Asserted `build_system()` returns two `ephemeral`-marked blocks, and that the
  instructions block is byte-identical before/after appending a fact while the
  athlete block changes.
- Ran `reply()` end-to-end with a fake LLM (`save_fact` in round 1, text in
  round 2): the instructions block is identical across rounds, the athlete
  block differs, the fact persists, and both rounds log usage.
