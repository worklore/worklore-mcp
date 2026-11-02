# Prompt caching vs. save_fact

## Why every save_fact paid full price

`build_system()` sent one system block holding the instructions, the athlete's
context and the facts, with a single `cache_control` marker at the end.
`save_fact` adds to `a.facts` partway through `reply()`, and the system prompt was
rebuilt on every loop round. So the very next round (and later the next message)
sent a different block. The only cache entry covered the whole block, so it was
lost and ~1000 tokens were written again. In `logs/usage.jsonl`, every round that
follows a `save_fact` has `cache_read_input_tokens: 0` and a full `cache_creation`.

Just moving the marker to the end of the instructions would not work.
Tools + instructions come to roughly 950–1000 tokens. That is probably below
Sonnet 4.5's 1024-token minimum for caching. If so, the marker is silently
ignored and nothing gets cached at all.

## What changed (bot.py only)

1. **The system prompt is now split into blocks, static parts first:**
   coaching rules → athlete profile (name, sport, zones, goal, language) →
   one block per fact → today's date.
   - Marker 1 is on the profile block. Rules + profile stay byte-identical across
     messages and across `save_fact`.
   - Marker 2 is on the last fact. Facts are only ever appended, so the previous
     request's cached prefix (ending at the old last fact) is still a prefix of the
     new request. The API's cache lookback (~20 blocks back from a marker) finds
     it. After a `save_fact`, the next call reads the old prefix from cache and
     writes only the new fact. This prefix is also above the 1024 minimum, so it
     doesn't depend on marker 1 being cacheable.
   - The date moved after the last marker, so a change of day no longer
     invalidates the cache either. "(none yet)" is its own block after the
     profile, so saving the first fact doesn't change the profile text.
2. **The system prompt is built once per `reply()`** instead of once per round.
   The model already has the new fact in its own tool call, so tool-loop rounds
   now send identical prompts and get full cache reads. The next message picks up
   the fact.
3. `build_request()` now takes the prebuilt `system`. `athlete_context()` became
   `athlete_profile()`.

The prompt text the model sees is the same apart from the order (the date and
language lines moved).

## How it was checked

I made no API calls. I ran a fake-client script (outside the repo) through five
messages, two of them with `save_fact`. It checked that:
- the rules and profile blocks never change,
- each request starts with the previous request's cached prefix,
- prompts within one message are identical,
- there are at most 4 markers.

To check it for real, compare `logs/usage.jsonl` after deploy. The call after a
`save_fact` should show `cache_read_input_tokens` ≈ the old total and
`cache_creation_input_tokens` of only a few dozen tokens.

## Not changed / worth knowing

- **Tool filtering also breaks the cache.** Tools come before the system prompt
  in the cached prefix. A message that adds or drops `plan_week`/`predict_race`
  compared with the previous one misses the cache too (e.g. the `plan_week` line
  in the log). NOTES.md says to keep the filtering, so I left it. If that cost
  matters, the fix is to always send the same tool list.
- An athlete with no facts gets a prefix of rules + profile only. That may be
  under 1024 tokens and so not cached. This is no worse than before in practice.
- **Secrets in the repo:** README.md contains what looks like a real
  `COACH_ANTHROPIC_KEY`, and `config/bot.toml` has the Telegram token. I didn't
  touch them, but they should be revoked/rotated and removed from git history.
