# Fix: memory writes evicting the static system prompt

## Cause

`build_system()` in `bot.py` returned one text block: `INSTRUCTIONS` plus the
per-athlete context (date, profile, zones, goal, facts, language), with a single
`cache_control` marker at the end. Caching is a prefix hash, so every `save_fact`
changed the facts inside that block, changed the hash, and evicted the whole
prompt, including the instructions that never change.

`logs/usage.jsonl` shows it. The call after a `save_fact` has
`cache_read_input_tokens: 0` and `cache_creation_input_tokens` around the full
prompt size (about 1050 to 1100 tokens), for example the `save_fact` rounds at
2026-04-18 06:43:16 and 08:02:33.

## Change

`bot.py`, `build_system()`: the system prompt is now two text blocks, each with
`cache_control: {"type": "ephemeral"}`:

1. `INSTRUCTIONS`, a constant. Byte-identical across athletes, days and memory writes.
2. `athlete_context(a, today)`, the volatile tail.

A `save_fact` write now invalidates only block 2. Block 1 should still be read
from cache. Checked offline: block 1 is identical for two athletes on different
days and after a fact is added, and block 2 changes.

`README.md`: the caching paragraph described the single marker. It now describes
the two-block layout.

Nothing else changed. Tool selection, the save path and the tool loop are as before.

## Which parts of the colleague's note applied

- **Applied: two `cache_control` markers, static instructions first, per-user tail second.**
  This is the same fix, and the `build_system` comment records the rule that
  `INSTRUCTIONS` must stay free of interpolated values.
- **Applied: the check to run.** Send two messages within 5 minutes, then one that
  triggers `save_fact`, then one more. The last call should show `cache_read` covering
  the static block and `cache_creation` near the tail size only. If `cache_creation`
  is the full prompt size again, something in block 1 is not byte-stable.
- **Applied, with a caveat: keep the tools array stable.** `save_fact` and `log_session`
  are always sent, so memory writes don't change the tools. The keyword groups
  (`plan_week`, `predict_race`) do change the tools array, which sits above the system
  prompt in the cache prefix. The usage log shows this: the `plan_week` call at
  06:44:31 has `cache_read_input_tokens: 0`. I did not change this. Fixing it means
  either sending all tools every time, which gives up the keyword-filter saving, or
  accepting the occasional re-cache. The colleague's note makes the same trade-off.
- **Not applied: top-N fact selection.** This bot already loads all facts every time,
  so there was nothing to change.
- **Not applied: the 780 / 240 token figures and the Telegram setup.** Those are their
  numbers for their bot. The Telegram transport is not in this repo.

## Open risk: the minimum cacheable length

The first block may be below the minimum cacheable prompt length. To my knowledge
that minimum is 1024 tokens for Sonnet-class models, so please check it against the
docs. The static prefix is `INSTRUCTIONS` (about 2,480 characters, roughly 620 tokens by
a chars/4 estimate) plus the core tool schemas (about 420 characters of JSON). That is
probably around 750 to 900 tokens, under 1024. If so, the marker on block 1 is ignored
silently, and a memory write will still re-cache everything: nothing breaks, but the
fix does nothing.

I could not check this. There is no API key in the sandbox, and I have not called the
API. The check that settles it is `messages.count_tokens` on the tools plus the static
block, or the first real `save_fact` after deploy. If `cache_creation` after the write
is about the tail size, the fix works. If it is about the full prompt again and the
static block is under the minimum, the options are: make the instructions substantially
longer with real content (a product decision, not a padding trick), or accept the
re-cache.

## Verification status

- Offline check: passed, as described above.
- Live API check: not done. Needs a key and the steps under "Open risk".
- Not committed. The working tree has `bot.py` and `README.md` modified, plus this file.
