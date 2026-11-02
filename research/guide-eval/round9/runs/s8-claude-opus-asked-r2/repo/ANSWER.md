# Prompt caching vs. save_fact — what changed

## Why it broke

`logs/usage.jsonl` shows the same pattern every time: the round right after a
`save_fact` reads 0 from cache and writes the whole prompt again (~1000 tokens).
There were two causes in `bot.py`:

1. **The system prompt was rebuilt on every tool-loop round.** `run_tool` adds the
   new fact to `a.facts`, and the next round called `build_system(a, today)` again.
   So the prompt changed in the middle of a single reply.
2. **The whole system prompt was one cached block**: instructions plus the athlete
   context, with the facts in the middle (before `Language:`). The cache matches on
   an exact prefix, so changing any byte of that block meant none of it could be
   read from cache, including the instructions, which never change.

## What changed (`bot.py`)

- **The system prompt is built once per message** in `reply()` and the same copy
  is sent on every loop round. `build_request` now takes `system` instead of
  rebuilding it. The model still knows about the new fact from its own
  `save_fact` call in the message history.
- **The system prompt is now a list of blocks, set up so that adding a fact only
  adds to the end:**

  ```
  [INSTRUCTIONS]*  [date + profile + zones + goal + language]  [- fact 1] ... [- fact N]*
  ```
  `*` = `cache_control: ephemeral` (2 of the 4 allowed markers).
  - The instructions get their own marker and are byte-identical for all users
    and all days.
  - Each fact is its own block, and the facts come last. After a `save_fact`, the
    previous request's cached prefix (which ended at the old last fact) still
    matches the start of the new request exactly. The API checks for cache hits at
    earlier block boundaries, so it reads that prefix from cache and only writes
    the new fact block (~15 tokens) instead of ~1000.
  - `Language:` moved above the facts, and the `- (none yet)` placeholder is gone.
    The first fact would have replaced it and broken the prefix.
- Tool keyword filtering is unchanged, as NOTES.md asks.

## Expected effect

| call | before | after |
|---|---|---|
| loop round after `save_fact` | write ~1000, read 0 | read ~1000, write 0 |
| next message after `save_fact` | read ~1000 | read ~1000, write ~15 (new fact) |

## Caveats

- **Tools come before the system prompt in the cached prefix.** A message that
  matches a keyword and adds the plan/race tools still misses once (for example
  the 1305/1334-token writes in the log). That cost comes from tool filtering, not
  from memory. Within one message the tool list doesn't change, so loop rounds
  still hit.
- **The instructions marker may be too short to cache on its own.** Sonnet 4.5
  only caches a prefix of at least 1024 tokens. Tools plus instructions come to
  about 800 tokens, so that marker probably does nothing on this model, and the
  memory fix doesn't rely on it. It only helps for a new user or on a new day once
  that prefix is long enough.
- The date line is part of the profile block, so the first message of each day
  writes the athlete tail again (once a day, as before).
- The block-boundary lookback covers about 20 blocks. Facts are added one or two
  per message, so that is far more than needed.

## How I checked

Offline only (no API calls). A fake LLM ran a `save_fact` reply plus one follow-up
message. Both loop rounds sent the exact same `system`. The next message's blocks
were the previous ones plus one new fact block at the end. `data/` and `logs/`
were not touched. To confirm on the real API, look at the next `usage.jsonl`
lines after a `save_fact`: round 2 should show `cache_read_input_tokens` ≈ the
full prompt, and the next message a small `cache_creation_input_tokens`.
