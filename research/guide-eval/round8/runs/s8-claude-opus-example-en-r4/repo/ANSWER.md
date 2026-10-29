# Fix: a save_fact no longer evicts the cached system prompt

## What was wrong
`build_system()` sent the whole prompt as one text block with a single `cache_control`
marker: instructions + profile + facts, with `Language:` after the facts and `Today:` at the top
of the athlete part. The cache works on prefixes, so appending a fact changed the content of the one
cached block. That meant a miss on all of it (~1050 tokens). `logs/usage.jsonl` shows this
on every `save_fact`. It isn't the *next message* that pays; it's **round 2 of the same tool loop**:
`reply()` changes `a.facts` in place, so the round after `save_fact` rebuilds the prompt with
the new fact (`cache_read 0, cache_creation ~1061`). The date line in that same block also
caused one full miss per athlete per day.

## What I changed (`bot.py`, `build_system` / new `athlete_profile`)
System is now a list of blocks:

1. **Instructions + stable profile** (name, sport, zones, goal, language, facts header): this has
   `cache_control` and contains no dates or counters.
2. **One text block per fact**, in save order. The last one has `cache_control`.
3. **`Today: …`**: this comes after the last marker, so it's always uncached (~15 tokens) and a new
   day doesn't invalidate anything.

Why this works even though the static part is short: `save_fact` only appends. The prefix
the previous request cached (ending at the old last fact) is therefore still a prefix of the new
request, and it ends on a block boundary. The API checks earlier block boundaries (up to 20) for
existing cache entries, so the new request reads everything up to the old last fact from cache.
Only the new fact is written (~15 tokens instead of ~1050). The "(none yet)" placeholder was
removed because replacing it would have broken the prefix on the first fact. That means the
prompt wording changed slightly ("Long-term facts (one per line below; may be empty):", and
Language moved above the facts).

Nothing else changed: tool filtering, model, loop and the athlete file format are as before.

## Verification
- Added `tests/test_cache_layout.py` (offline, no API key needed). It uses a fake client that models
  the documented prefix-cache rules (an entry written at each breakpoint, a 20-block lookback, tools
  before system). It checks three things: (a) after `save_fact`, the next round's cache write is under
  5% of the prompt and the read is over 95%; (b) a date change writes nothing; (c) the static
  block is byte-identical across days and facts.
  `python3 -m unittest discover -s tests` passes 3/3. On the original `bot.py` all 3 fail.
- **Not run against the real API** (no key, and the SDK isn't installed here). The token numbers in
  the test come from a chars/4 estimate. To confirm in production, send a message, then one that
  triggers `save_fact`. Round 2 should show `cache_read_input_tokens` ≈ the previous prompt and
  `cache_creation_input_tokens` ≈ the size of one fact.

## Which parts of the colleague's note applied
- **Applied:** splitting the system prompt into a byte-stable instruction segment and a volatile
  tail, each with a `cache_control` marker (2 of the 4 allowed). The same for "keep the static block
  free of interpolated dates/names/counters": I moved `Today:` out of the cached part entirely.
  "Load all facts, don't do top-N selection" also applied, and the code already did it. Reading
  `usage` per call to diagnose applied too: that's how the round-2 miss showed up.
- **Didn't carry over as-is:** the note's two markers alone would probably *not* have fixed this bot.
  Sonnet 4.5 only caches a prefix of at least 1024 tokens. Here tools + instructions + profile is
  roughly 950–1000 tokens (the whole prompt is ~1024–1046 for athletes with 2–3 facts). So a marker
  after the static segment may simply not create a cache entry, and then every fact write would still
  re-cache the full prompt. The fix that doesn't depend on that threshold is one block per fact plus
  block-boundary lookback. I kept the static-segment marker anyway: it does no harm if it's below the
  minimum, and it helps if the instructions grow or a profile field is edited.
  Also, the note's "date in the volatile tail" would still make the facts miss once a day. Putting
  the date after the last marker avoids that.
- **Not applicable / left alone:** tool filtering. Per NOTES.md it stays. Tools come before
  system, so a message that adds the `plan`/`race` group still re-caches the whole prompt once
  (the 1305/1334 rows in the log). Within one message's loop the tool list doesn't change, so the
  loop rounds still hit. The MCP and Telegram details in the note don't apply to this repo.

## Remaining caveats
- If facts are ever edited or deleted (not possible today), everything after the changed fact is
  re-cached. Keep `save_fact` append-only.
- The lookback reaches back 20 blocks, so one message saving more than ~20 facts at once would miss.
  That isn't realistic with "call save_fact once".
