# Why every save_fact was a full cache miss, and the fix

## Cause
`build_system()` sent the system prompt as **one** text block with one
`cache_control` marker: instructions + `Today:` + profile + facts + `Language:`.
Prompt caching only matches exact prefixes, so changing any byte of that block
throws away the cache entry for the whole block. `save_fact` appends to
`a.facts`, and the loop rebuilds the system prompt on the next round, so the
round right after a `save_fact` sent a different block. That's the
`cache_read_input_tokens: 0` / `cache_creation ≈ 1000+` pattern in
`logs/usage.jsonl`, and those writes cost 1.25x base input instead of 0.1x.
The `Language:` line also came after the facts, so a new fact never just
extended the old prompt. It changed the middle of it.

The obvious fix doesn't work here. If you split off the instructions as their
own cached block, nothing gets cached: tools + instructions come to about
960 tokens (the logs show ~1046 total for athlete 42, and the profile and 3 facts
are ~85 of that). Sonnet 4.5 needs at least 1024 tokens before a breakpoint,
and anything shorter is silently not cached.

## Change (`bot.py`, `build_system` / new `athlete_profile`)
The system prompt is now a list of blocks, ordered so the parts that change most
come last:

1. `INSTRUCTIONS`: static
2. profile (name, sport, zones, goal, language, a "facts follow" header): stable per athlete
3. one block per fact (`save_fact` only ever appends)
4. `Today: …`: after the last breakpoint, so it isn't cached

The `cache_control` breakpoint is on the **last fact block**. When a fact is
appended, the old prompt is an exact prefix of the new one, and the old
breakpoint is one block earlier. The API's prefix lookback (up to 20 blocks
before a breakpoint) finds the previous entry. So the call after a
`save_fact` reads the ~1000 cached tokens and writes only the new fact
(~15 tokens), instead of re-writing everything.

Side effects:
- The date moved out of the cached part, so the first message of each day no
  longer misses the cache either.
- A second breakpoint on the profile block is a fallback for when facts are
  edited or removed, or more than 20 are added between two calls. It only
  takes effect if tools + instructions + profile reach 1024 tokens; otherwise
  it does nothing and costs nothing.
- `(none yet)` is gone. If it disappeared when the first fact arrived, the
  prompt would no longer be append-only.

Tool filtering is unchanged, as NOTES.md asks.

## Verification
I ran it offline with a fake LLM client (no API calls): `reply()` with a
`save_fact` round, then another message. For each request, the prefix up to the
previous request's last breakpoint is byte-identical in the next request (the
round after save_fact, and the following message). The final system text reads
the same as before, apart from the order.

I haven't checked it against the live API. After deploying, watch
`logs/usage.jsonl`: rows right after a `save_fact` should show
`cache_read_input_tokens` ≈ the previous prefix and a small
`cache_creation_input_tokens`.

## Not fixed (separate issue)
Tools come before `system` in the cache prefix. When a message's keywords pull
in `plan_week` / `predict_race`, the tool list changes and the whole prefix
misses (the 1305/1334 rows). That isn't caused by memory writes, and NOTES.md
asks to keep keyword filtering. If it matters, one option is to always send the
same tool list and limit which tools can be used per message instead.
