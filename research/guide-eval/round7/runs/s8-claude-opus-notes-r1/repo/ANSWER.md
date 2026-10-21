# Prompt caching vs. save_fact

## What was wrong

`build_system` sent the system prompt as one block with one `cache_control` marker:
the instructions plus the athlete tail (date, profile, facts, language). Prompt
caching matches on the prefix, so when `save_fact` added a line to the facts the
block's hash changed. The next call (round 2 of the same reply in
`logs/usage.jsonl`) found nothing cached and wrote all ~1050–1100 tokens again
(`cache_read_input_tokens: 0`), static instructions included.

## Why "just add a second marker after the instructions" isn't enough here

The usual fix is two segments: instructions | volatile tail. But on Sonnet 4.5 a
cache entry is only written if the prefix is at least **1024 tokens**. Tools come
before `system` in the prefix. With the default tool set (`save_fact` + `log_session`)
the tools plus instructions come to about **940 tokens**: users 77 and 42 cache 1024
and 1046 tokens in total, and their tails are about 85–110 tokens. That falls below
the minimum, so the API would silently skip a marker on the instructions, and a
memory write would still re-cache the whole prompt on most messages. The
simulation below shows this: the two-segment version gives read 0 / write 1061
after a save.

## What I changed (`bot.py`)

- `athlete_context` now returns a list of blocks instead of one string, ordered
  from most stable to least stable: profile (name, sport, zones, goal, language),
  then today's date and the facts header, then **one block per fact**. `Language`
  moved up from the end. The `(none yet)` placeholder is gone; the header now says
  the list may be empty. Otherwise the first fact would replace a line instead of
  appending one.
- `build_system` sends `INSTRUCTIONS` as its own block with a marker (byte-identical
  for all users and days) and puts the second marker on the **last** block.
- Facts are append-only (`save_fact` appends), so after a memory write the previous
  request's prompt is still an exact block-by-block prefix of the new one. The API
  checks for cache hits at earlier block boundaries (up to about 20 blocks back)
  from a marker, so the new request reads the whole old prompt from cache and
  writes only the new fact (~15 tokens). This doesn't depend on the 1024-token
  minimum because the full prompt is already above it. The instructions marker
  still helps when a tool group pushes the static part over 1024, and lets that
  part be shared between users.
- Two markers per request (the limit is 4). Tools, tool filtering and the loop are
  unchanged. NOTES.md says to keep the keyword filtering.

## Verification (offline, no API calls)

`python3 -I tests/test_prompt_cache.py` simulates prefix caching: entries are
written at markers when the prefix is at least 1024 tokens, with a 20-block
lookback. Token counts are estimated from character counts plus a fixed overhead
fitted to `logs/usage.jsonl`. The test also checks that a save only appends
blocks, that the instructions block is identical across users and dates, and that
there are no more than 4 markers.

| after a save_fact | read | write |
|---|---|---|
| before (one block) | 0 | ~1060 |
| plain two segments | 0 | ~1060 (static part below 1024) |
| now | ~1047 | ~14 |

On the live bot, check the logs: the round right after a `save_fact` should show
`cache_read_input_tokens` ≈ the previous value and `cache_creation_input_tokens`
≈ 15–30. I didn't run it against the real API, so this is the simulation's
prediction, not a measured result.

## Caveats

- Don't edit or delete facts in place, and don't select a subset of facts per
  message. Either one breaks the "only append" property and causes a full re-write.
  If editing facts is added later, expect one full re-cache per edit.
- A message that adds a tool group (plan/race) changes the tools at the front of
  the prefix and re-caches everything once. That was already true before this
  change and is the cost of keeping the filtering.
- The date sits above the facts, so the first message after midnight re-caches
  the tail. That's harmless with a 5-minute TTL.
- A brand-new athlete with no facts on the default tools is around 1000 tokens,
  which may be under the 1024 minimum and not cached at all. That was already the
  case before this change; it goes away after the first fact or two.
