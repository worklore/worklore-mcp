# Fix: memory writes no longer evict the cached system prompt

## Root cause

`build_system` concatenated the static `INSTRUCTIONS` and the volatile per-athlete
context (which contains the long-term facts list that `save_fact` appends to) into a
single prompt-caching block. Anthropic's cache is a prefix hash, so one appended fact
changed the whole block: the very next API call (round 2 of the same tool loop) found
no matching cache entry and re-created ~1000 tokens at cache-write price
(1.25x input) instead of reading them from cache (0.1x). That is exactly the pattern
in `logs/usage.jsonl`: every round right after a `save_fact` shows
`cache_read_input_tokens: 0` and `cache_creation_input_tokens` back up at ~1000–1100.

A second, subtler problem: the system prompt was rebuilt from the athlete record on
every round of the tool loop, so the `save_fact` that ran in round 1 mutated
`a.facts` and changed the prompt mid-loop.

## What changed (all in bot.py)

1. **Two cache blocks instead of one** (`build_system`, bot.py:135). The system
   prompt is now two `cache_control`-marked text blocks, volatile part last:
   - Block 1: `INSTRUCTIONS` + stable profile header (name, zones, goal, language —
     everything a memory write does not touch), built by the new
     `profile_context` (bot.py:117).
   - Block 2: the date + `Long-term facts` list, built by the new
     `facts_context` (bot.py:128).
   A `save_fact` now only invalidates the small second block (~60–120 tokens),
   never the static instructions. Moving the date into block 2 also means a new day
   costs one small block re-creation instead of a full one.

2. **System prompt snapshotted once per message** (`reply`, bot.py:205–213;
   `build_request` now takes the prebuilt array, bot.py:201). The prompt is built
   before the tool loop and the same array is reused for every round, so a memory
   write can no longer change the request prefix mid-loop. The new fact still enters
   the prompt with the next message — the same promise as before ("the next message
   sees the fact"), and round 2 already knows the fact from the tool result.

## Effect

- The round following a `save_fact` now sends a byte-identical prefix, so it reads
  the cached instructions at 0.1x instead of re-creating ~1000 tokens at 1.25x.
- On the next message, only block 2 (date + facts, ~60–120 tokens) is re-created;
  the ~900-token instructions + header block stays cached. On the save path that is
  roughly a 90–95% cut in cache-write tokens, and cache reads go up correspondingly.
- If the profile ever changes (zones, goal), block 1 is rebuilt once — correct
  behavior, same as before.

## Caveat: Anthropic's 1024-token minimum

For `claude-sonnet-4-5` a cache breakpoint whose prefix is under 1024 tokens is
silently ignored (no error, just no caching). Block 1 (tools + instructions +
header) is estimated at ~950–1070 tokens — today's *whole* system measures
1046–1104 in `logs/usage.jsonl`, and block 1 is only the ~60–120 volatile tokens
smaller — so it sits at the threshold. This is why the volatile block was kept
*last*: if block 1 ever falls under the minimum, its marker is skipped and block 2
behaves exactly like the old single block (prefix ≈ 1046+ tokens, which is known to
cache). The design degrades to today's behavior rather than below it; the mid-loop
snapshot in fix 2 alone guarantees the "call after save_fact reads from cache"
property either way.

## Verification (no external calls)

Ran an inline test with a fake LLM (temp `data/athletes.json` / `logs/usage.jsonl`;
real files untouched, confirmed via `git status`):

- Across a `save_fact` tool loop, the system array sent to the API is byte-identical
  in rounds 1 and 2 (before the fix it differed).
- Both blocks carry `cache_control: ephemeral`; facts/date appear only in block 2;
  the fact is still persisted and appears in block 2 of the *next* message while
  block 1 stays byte-identical.
- A calibrated simulation of Anthropic prefix caching (writes only at breakpoints,
  backward lookback, 1024 minimum) over normal → save_fact → normal messages:
  block 1 over the minimum → cache-created tokens 2272 (old) vs 1193 (new);
  block 1 under the minimum → identical to old (graceful degradation).

Also updated NOTES.md with a 2026-11-09 resolution entry.
