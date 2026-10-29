# Why save_fact evicted the cache, and the fix

## Cause
`build_system()` sent the whole system prompt as **one** text block with one
`cache_control` marker at its end, and the long-term facts sat in the middle of it
(followed by `Language:`). Prompt caching matches exact prefixes at block
boundaries, so appending a fact changed the only cached block: the call after a
`save_fact` (round 2 of the same message, since `run_tool` mutates the athlete and
the loop rebuilds the prompt) found nothing to reuse and paid
`cache_creation_input_tokens` for all ~1000 tokens again. That is exactly the
`round 2 … cache_read 0` line after every `save_fact` in `logs/usage.jsonl`.

Splitting off just the instructions with their own marker would not have worked:
tools + instructions + profile are ~990 tokens, below the 1024-token minimum
cacheable prefix for Sonnet 4.5, so that breakpoint would be silently ignored.

## Change (`bot.py`, `build_system` / new `athlete_profile`)
The system prompt is now an append-only list of blocks:

1. instructions + stable profile (name, sport, zones, goal, language, "Long-term facts:" header)
2. one block per fact; `cache_control` goes on the last one (or on block 1 if there are no facts)
3. a volatile tail after the marker: today's date and "(none yet)" when there are no facts

When a fact is added, every earlier block is byte-identical and the marker moves to
the new last block. The API's automatic lookback over earlier block boundaries
(~20 blocks) finds the entry written by the previous call, so it reads ~1050
tokens from cache and writes only the new fact (~20 tokens). `Language:` moved
above the facts and `Today:` moved after the marker, so the date rolling over at
midnight no longer evicts the cache either. The model sees the same information.
Tool filtering is unchanged, as NOTES.md asks. README updated to describe the layout.

## Verification
I had no API key, so I ran a local simulation: a fake LLM implementing prefix
matching, the 20-block lookback and the 1024-token minimum, with token counts
calibrated to the logged 1046. It replayed a chat with two `save_fact`s.
- Original code: the call after each save_fact gets read 0, create ~1130 (matches the log).
- New code: the call after each save_fact gets read ~1100–1156, create ~20–24.

This should be confirmed against real `logs/usage.jsonl` numbers after the next run.

## Not changed / caveats
- Tools come before the system prompt in the cache prefix, so messages that pull in
  the plan or race tool group still use a separate cache entry per tool combination
  (e.g. the 1305-token write on the plan_week message in the log). That cost was
  already there before memory and is the trade-off from keyword filtering.
- A brand-new athlete with no facts is just under 1024 tokens and is not cached at all
  (same as before). Caching starts after a fact or two.
- The lookback only covers about 20 blocks. If one message saved more than ~20 facts
  at once it would miss, which is unrealistic with one fact per message.
