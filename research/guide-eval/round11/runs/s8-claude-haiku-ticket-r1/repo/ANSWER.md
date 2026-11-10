# Fix: a `save_fact` write no longer evicts the static instructions

## Cause

`build_system()` returned one text block containing `INSTRUCTIONS` plus the
per-athlete context (date, profile, zones, goal, facts, language), with a single
`cache_control` marker at the end. Prompt caching matches the prefix up to a
marker, so any change to the facts changed the whole cached prefix. Every
`save_fact` therefore forced the next call to re-create the entire prompt.

`logs/usage.jsonl` shows it: each `save_fact` round is followed by a call with
`cache_read_input_tokens: 0` and `cache_creation_input_tokens` around 1000 to 1300,
even though `INSTRUCTIONS` never changed.

## Change (`bot.py`, `build_system`)

The system prompt is now two text blocks, each with its own marker:

1. `INSTRUCTIONS`. Constant text. Byte-identical for every athlete and every day,
   so a fact write never touches it.
2. `athlete_context(a, today)`. Date, profile, zones, goal, facts, language.
   This is the only block that changes on `save_fact` or at midnight.

The static block comes first. The prefix match then stops at the static marker
for every request, whatever the facts are. Nothing else changed: tools, the
tool loop, fact storage, and the "all facts every time" behaviour are the same.

Checked with a fake LLM and temp copies of the data and log files (the real
`logs/usage.jsonl` and `data/athletes.json` were not touched):

- the static block is identical before and after a `save_fact`, and on the next day
- only the athlete block changes, and it contains the new fact
- two markers are used, out of the four allowed

## Open risk: the static block may be under the cache minimum

Caching only happens for a prefix of at least 1024 tokens on Sonnet models. The
prefix a marker covers is the tool schemas (they come before `system`) plus the
text up to the marker. My estimate, which is not the Claude tokenizer and needs
checking:

- `INSTRUCTIONS`: ~710 tokens
- core tools (`save_fact`, `log_session`): ~120 tokens
- static prefix: ~830 tokens (~890 when a planning tool is included)

That is under 1024. If so, the static marker is silently ignored (no error, just
`cache_creation` = 0 on that block), and the fix only partly works.

To make it work, `INSTRUCTIONS` needs roughly 200 more tokens of real content.
I did not pad it with filler, because the coaching rules are a product decision.

How to check on the next deploy: after a `save_fact`, `cache_creation_input_tokens`
should be roughly the size of the athlete block (~200 tokens), not the whole prompt
(~1000+). If it is still ~1000+, the static block is still under the minimum.

## Notes from the colleague's writeup

Applied:
- Two text blocks with separate `cache_control` markers, static block first. This is
  the core of the fix.
- Byte-stable static text: no dates, names or counters in `INSTRUCTIONS`.
- Keeping all facts loaded every time, rather than selecting per message. We already
  do this, and I left it alone.
- Using the `usage` fields to tell cache creation from reads (the check above).

Not applied, or not applicable:
- Their figures (~780 static / ~240 tail) are their own. Ours are ~620 static
  (estimated) and ~200 tail.
- Their static block may have been above the minimum because of the tool schemas.
  Ours is probably not, as explained above.
- Tool filtering: already in place here (`select_tools`). I did not change it. One
  side effect remains: the tools sit in the cached prefix, so a message that adds a
  keyword group (`plan`, `race`) starts a different prefix, and its first call
  re-creates the cache. Within a message's tool loop the tool list is constant, so
  rounds 2+ still hit.
- Rebuilding the athlete block every round means a `save_fact` mid-loop changes it
  for the next round (one small re-creation). I kept this on purpose: freezing the
  block for the loop would hide the just-saved fact from the model, and rule 16
  (no duplicate saves) depends on it seeing the current list.
- Telegram transport, marker-count tuning beyond two, and marker syntax: not
  relevant to this repo.

## Not done

- No API calls were made, so the cache behaviour is unverified against the live
  API. The local checks above only cover prompt structure.
- Nothing committed.
