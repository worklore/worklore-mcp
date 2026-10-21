# Fix: a save_fact no longer evicts the cached system prompt

## What was wrong

`build_system()` returned **one** text block (instructions + date + profile +
facts) with one `cache_control` marker at the end. The prompt cache matches on
an exact prefix, so changing any byte in that block (a new fact, the date)
made the whole block a miss. `reply()` rebuilds the system prompt on every
tool-loop round. `save_fact` adds to `a.facts` during the loop, so the miss
happens **in round 2 of the same message**. That's the pattern in
`logs/usage.jsonl`: every round after a `save_fact` has `cache_read 0` and
`cache_creation` ≈ the whole prompt (1039–1104 tokens).

## What I changed

`bot.py`, `build_system()` now returns blocks ordered from never-changing to
most-changing, with 3 of the 4 allowed markers:

1. `INSTRUCTIONS`: byte-identical for every athlete and every day. **Marker.**
2. Profile: date, name, sport, zones, goal, language, `Long-term facts:` header. **Marker.**
3. One block per fact (`- fact\n`), or `- (none yet)`. **Marker on the last block.**

`save_fact` already only appends, so a new fact becomes a new block after
the previous marker. The API checks block boundaries up to ~20 blocks back
from a marker, finds the previous request's cache entry one block back, reads
all of it, and writes only the new fact (~15 tokens). If facts are ever edited
or reordered, or the date changes, the profile marker (and below that the
instructions marker) still limits what gets re-cached.

Other changes:
- `Language:` moved up from the end of the context into the profile block,
  so facts are the only thing after the profile.
- `README.md`: the caching sentence now describes the new layout.
- `tests/test_cache_layout.py`: offline test with a fake client that copies
  prefix-cache rules (entries written at markers, 20-block lookback). It
  checks that (a) the instructions block is identical across athletes and
  dates, (b) the round after a `save_fact` reads the whole earlier prompt
  from cache and writes only the new fact block, and (c) a new day keeps the
  instructions cached. Run it with `python3 -m unittest tests/test_cache_layout.py`.
  All 3 pass on the new code and all 3 fail on the old code.

I didn't change tool filtering or the loop itself. I didn't call the real API
(no key, and I stayed off external services).

## Check this in production

The fake client counts characters, not tokens, and doesn't enforce the
**minimum cacheable length**. For `claude-sonnet-4-5` that's 1024 tokens,
counted on the whole prefix up to a marker (tools + system).
- The facts marker covers about what the old single marker did (~1020–1100
  tokens in the log), so it caches as before. It's still borderline:
  athlete 77 was at exactly 1024 with 2 facts. An athlete with no facts may
  fall just under 1024 and not be cached at all, with the old code or the new.
- The instructions and profile markers are probably under 1024 on their own
  (my estimate is ~900–1000 tokens with the core tools). If so, the API
  ignores them and nothing breaks. They only start working if the prefix
  grows. So the gain from this change is in the common append-a-fact case,
  through the lookback. A new day or an edited fact would still re-cache
  the full prompt until the static part reaches 1024 tokens.

How to verify with a key: in `logs/usage.jsonl`, the round after a `save_fact`
should now show `cache_read` ≈ the previous prompt size and `cache_creation`
≈ 10–30 tokens. If it still shows ~1000 created, something volatile has got
into an earlier block.

Something in the log I couldn't explain: at `08:03:24` a `predict_race` round 1
reads 1090 from cache, but round 2 creates 1334. Tools are chosen once per
message, so the two rounds should have the same prefix. Worth a look if it
happens again. Messages with extra tool groups (plan/race) are full misses
by design, because tools sit before the system prompt. That's the trade-off
already noted in NOTES.md, and I left it alone.

## Which parts of the colleague's note applied

- **Applied:** the diagnosis (prefix hash, one marker, a memory write evicts
  the static instructions). Using more than one `cache_control` marker. A
  byte-stable instructions block with nothing interpolated (date, name,
  counters). Keeping tools above the system prompt stable and keeping the
  keyword filtering as it is (NOTES.md says the same). Loading all facts
  instead of a top-N selection, which the code already did. Reading
  `usage` to verify.
- **Adapted:** the note says to put "everything volatile" in **one** tail
  block. Here that wouldn't be enough. Instructions (~780 tokens) + tools is
  probably below Sonnet 4.5's 1024-token minimum, so a marker after the
  instructions alone may never cache, and every `save_fact` would still
  re-cache the full prompt. Giving each fact its own block and relying on the
  lookback works whatever the static size. The note's "~240 tokens
  re-cached" becomes "only the new fact".
- **Didn't apply:** the MCP / ~55-tool-schema parts (this bot has 2–4 tools),
  the Telegram transport, and the cost figures. The note's "order the tail
  rarest-changing first, it's one hash anyway" is true for a single block.
  With per-fact blocks the order matters: facts have to be last and
  append-only.
