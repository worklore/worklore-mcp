# Why `save_fact` made the next call pay full price, and what changed

## Cause
`build_system()` joined the static coaching rules (~600 tokens) and the athlete
context, including the long-term facts, into **one** system block with **one**
`cache_control` breakpoint. The cache is a prefix match ending at a breakpoint, so when
the facts list changed (one new line), the whole block stopped matching: tools, rules and
everything else were written again (`cache_read 0`, `cache_creation ~1000+`). On top of
that, `reply()` rebuilt the system prompt on every tool round from the athlete object
that `save_fact` had just changed. So the miss came on round 2 of the same message,
which is exactly the "call right after a save_fact" in `logs/usage.jsonl`.

## Changes (bot.py)
1. **The system prompt is now split by how often each part changes.** It has three blocks,
   each with its own breakpoint:
   `INSTRUCTIONS` (static, the same for every athlete) → `athlete_profile()` (name,
   sport, zones, goal, language; edited by hand) → `athlete_memory()` (long-term facts +
   today's date). A new fact only invalidates the last block. The next call reads tools +
   rules + profile from cache and writes only the facts block (tens of tokens instead of
   ~1100). The "Today" line moved into the last block too, so the date changing at
   midnight no longer evicts the rules either.
2. **The system prompt is built once per message**, not once per tool round. The model
   already sees the saved fact in its own tool call, and the fact appears in the system
   prompt from the next message (as the README describes).
3. **The always-sent tools (`save_fact`, `log_session`) have real descriptions.** These
   are the usual 2–4 sentences with parameter descriptions. They say when to save a fact
   or log a session, which also helps the model choose correctly. This was needed for
   caching too. Sonnet 4.5 only caches a prefix of **at least 1024 tokens** and skips a
   breakpoint below that **without any error**. From the logs, Jonas's whole prompt with
   2 facts was exactly 1024 tokens, which puts tools + rules at ~930 and tools + rules +
   profile at ~990. Splitting the blocks alone would have cached nothing static, and every
   fact would still have re-written everything. The longer descriptions add ~190 tokens,
   bringing tools + rules to roughly 1100. That is an estimate from character counts. I
   could not measure it without calling the API.
4. **There is now a warning on stderr** whenever a call neither reads nor writes cache.
   That means the prefix is under the minimum, so a future trim of the rules or tools
   won't quietly turn caching off.

The keyword-based tool filtering is unchanged, as NOTES.md asks. Tools come before the
system prompt in the cache prefix, so each tool set (core / +plan / +race / both) still
has its own cache entry. That cost was already there and has nothing to do with memory.

README.md: updated the sentence about caching.

## How to check
Run a few messages including one that triggers `save_fact`. In `logs/usage.jsonl`, the
call after the fact should show `cache_read_input_tokens` of about 1100+ and only a small
`cache_creation_input_tokens`, not `0 / ~1100`. If a call shows both as 0 (and the stderr
warning prints), the static prefix fell under 1024 tokens. I checked locally with a fake
client that the system prompt stays the same within a message and that only the facts
block changes after `save_fact`. I did not make any real API calls.
