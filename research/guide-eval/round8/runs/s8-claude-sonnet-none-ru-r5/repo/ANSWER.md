# Fix: save_fact no longer invalidates the whole system prompt cache

## Cause
`build_system` put instructions, profile and facts into ONE text block with ONE
`cache_control`. A cache hit needs an identical prefix, so any new fact changed the block
and the whole prompt (~1000 tokens) was re-written at full price. The system prompt was
also rebuilt on every tool round, so round 2 after `save_fact` always missed (see the
`cache_creation_input_tokens ~1000` rows in logs/usage.jsonl).

## Changes (bot.py)
- `athlete_context` split into `athlete_profile` (name, zones, goal, language: rarely
  changes) and `athlete_memory` (today's date + facts: the volatile part).
- `build_system` returns two blocks, ordered stable -> volatile:
  1. INSTRUCTIONS + profile, with a cache breakpoint;
  2. date + facts, with its own breakpoint.
  A new fact now only invalidates block 2. The date also moved there, so the daily date change no longer busts the instructions.
- `reply()` builds the system prompt once per message and passes it to `build_request`,
  so a `save_fact` inside the tool loop does not change the prefix between rounds.

## Caveats (not verified: no API access here, nothing was run against the API)
- Minimum cacheable prefix on Sonnet 4.5 is 1024 tokens. From the log, tools + instructions
  are ~950 tokens by my estimate; with the profile (~70) the first breakpoint sits right at
  ~1020. If it falls below 1024 it is silently not cached and the savings disappear.
  Check logs/usage.jsonl after deploying: `cache_read_input_tokens` should stay > 0 on the
  call after a `save_fact`. If not, add a little static content (e.g. a few examples) to block 1.
- Tools come BEFORE system in the cache prefix. The keyword-based tool selection
  (plan_week / predict_race) changes the tool list between messages and busts the cache
  too (the 1305/1334 creation rows). I left it alone as NOTES.md asks; a fix would be
  to always send all tools (with a breakpoint on the last one), at the cost of the token saving.
