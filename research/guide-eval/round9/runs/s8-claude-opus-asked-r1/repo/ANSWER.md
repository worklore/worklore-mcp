# Fix: a `save_fact` no longer evicts the cached system prompt

## Cause

`build_system()` sent the whole system prompt as one text block with one
`cache_control` marker. The cache works on the exact prefix up to the marker.
`save_fact` appends to `a.facts`, and the facts sat inside that single block, so
the next call (round 2 of the same reply) had a different prefix. That is the
`cache_read_input_tokens: 0` / `cache_creation_input_tokens: ~1000` row after every
`save_fact` in `logs/usage.jsonl`.

## Why the usual fix (a second marker after the instructions) isn't enough here

Splitting into "static instructions [marker] + volatile tail [marker]" depends on
the static prefix (tools + instructions) being cacheable on its own. Sonnet's
minimum cacheable prefix is 1024 tokens. The log shows athlete 77's whole prompt,
with 2 facts and the profile included, at exactly 1024 tokens, so tools +
instructions alone come in under that. A marker there would be silently ignored,
and nothing would change.

## Change (`bot.py`, `build_system` and the new `athlete_profile`)

The system prompt is now a list of blocks, ordered from most to least stable:

1. `INSTRUCTIONS` + athlete profile (name, sport, zones, goal, language, the
   "Long-term facts" header). The "(none yet)" placeholder is gone, because the first
   fact would have had to replace it and that changes the prefix.
2. One block per fact, `- <fact>`. The `cache_control` marker goes on the **last**
   fact block, or on block 1 if there are no facts.
3. `Today: <date>`, after the marker, because it changes daily.

When it looks for a cached prefix, the API also checks the earlier block
boundaries before the marker (about 20 of them). After a `save_fact` there is one
extra block at the end, and the previous request's cache entry (instructions,
profile, older facts) is still an exact prefix one boundary back. So that entry is
read, and only the new fact (~15 tokens) is written. The cache size doesn't have
to cross 1024 again, because the earlier entry already did. The marker itself
isn't part of the cached content, so moving it is fine. This is the same thing
that makes the standard "marker on the last message" conversation caching work.

Nothing else changed: same model, same tools, and keyword tool filtering is left
in place as NOTES.md asks. The model still sees the new fact in its system prompt
on the next round and the next message.

## Verification

The `anthropic` SDK isn't installed here and I made no real API calls. I ran
`reply()` against a fake LLM that copies the cache rules (prefix hash per block,
write at the marker, look back ~20 boundaries, marker excluded from the hash),
using a temporary copy of `athletes.json`, which I then deleted. Results, in
approximate tokens:

```
round tool       create read
1     -          890    0      first message, cold
1     save_fact  0      890
2     -          13     890    previously create ~1000, read 0
1     -          0      903
1     save_fact  0      903
2     -          16     903
1     -          0      919
```

To check in production: after a `save_fact`, the next row in `logs/usage.jsonl`
should show `cache_read_input_tokens` of about the previous prompt size and
`cache_creation_input_tokens` of a few dozen tokens, not about 1000.

## Known, unchanged trade-off

Tools come before the system prompt in the cached prefix. A message that pulls in
the `plan` or `race` tool group still builds a separate cache entry for that tool
set once (the ~1305/1334 creations in the log). After that, the tool loop for that
message reads from cache. I kept this because the keyword filtering was a clear
win.
