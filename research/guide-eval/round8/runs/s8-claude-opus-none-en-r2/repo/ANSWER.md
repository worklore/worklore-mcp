# Prompt cache eviction on `save_fact`

## Cause

`build_system()` returned the system prompt as one text block with one
`cache_control` marker: `INSTRUCTIONS` + date + profile + the list of facts +
language. Prompt caching matches exact prefixes up to a breakpoint, and that
block ended in the facts list. So every `save_fact` changed the cached block and
the whole ~1000-token prefix (tools + instructions + profile) missed and had to
be written again. That happened twice: in round 2 of the same message, because
`run_tool` mutates `a.facts` and the loop rebuilds the system prompt every round,
and again on the next message. `logs/usage.jsonl` shows it: after every
`save_fact` the next call has `cache_read_input_tokens: 0` and
`cache_creation_input_tokens` ≈ 1046→1061→1075→… That is the full prefix, about
15 tokens bigger each time.

## Fix (`bot.py`, `build_system` / `athlete_profile`)

The system prompt is now several blocks, ordered from most stable to least:

1. `INSTRUCTIONS` + today's date + profile (name, sport, zones, goal, language)
   + the facts header. Breakpoint #1 goes here.
2. One text block per long-term fact (`"- fact\n"`), append-only, oldest first.
   Breakpoint #2 goes on the last fact.

`save_fact` only ever appends, so the new request still starts with exactly the
prefix the previous request cached. The API checks earlier block boundaries
(up to about 20 blocks) before a breakpoint, so it finds the entry written at
the old last fact. It reads ~1000 tokens from cache and writes only the new
fact (~15 tokens). This holds for the tool-loop round right after the save and
for the following messages.

Notes on the choices:
- The model sees the same text as before, in a slightly different order:
  "Language" moved into the profile, and the facts are listed last. The
  instruction "language from the profile below" still holds.
- I kept the date in the stable block and did not move it after the facts.
  Anything after the facts would break the append-only prefix. And everything
  after breakpoint #1 is too short to cache by itself: Sonnet 4.5 needs at
  least 1024 tokens per cached prefix, and tools + instructions alone come to
  about 970, which is under that. The date changes once a day, and the first
  message of a day is almost always a cold write anyway because of the
  5-minute TTL.
- Breakpoint #1 is a safety net in case facts are ever edited or removed
  instead of appended. For short profiles it may fall under the 1024-token
  minimum, in which case the API just skips it. That's harmless.
- I left keyword tool filtering alone, as NOTES.md asks. Be aware that tools
  come before the system prompt in the cache prefix. A message that adds
  `plan_week`/`predict_race` therefore still pays one full write for that
  tool set. You can see this as the 1305/1334 writes in the log. It is a
  separate cost from the memory issue.

## Verification

`tests/test_prompt_cache.py` (new, offline, no API calls) uses a fake LLM. The
fake applies the prefix/breakpoint/lookback rules and runs four messages,
including two `save_fact` calls. With the new layout, every call after the
first reads the full static prefix and writes fewer than 30 tokens. The test
passes. Against the original `bot.py` it fails with the symptom from the log:
round 2 after `save_fact` shows `cache_read 0` and a full re-write.

I did not make real API calls, so I haven't measured the actual numbers. Once
it is deployed, check `logs/usage.jsonl`: after a `save_fact` you should see
`cache_read_input_tokens` ≈ the previous prefix size and
`cache_creation_input_tokens` ≈ 15.

Also changed: the README paragraph on caching.
