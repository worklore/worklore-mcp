# Fix: a memory write should not evict the static instructions

## Cause

`build_system` returned one text block: instructions + athlete context (zones, goal,
facts, date, language), with one `cache_control` marker at the end. The cache matches by
prefix, so any change to that block (a new fact from `save_fact`) misses the whole block.
`logs/usage.jsonl` shows it: each call right after a `save_fact` has
`cache_read_input_tokens: 0` and `cache_creation_input_tokens` ≈ 1050–1100, which is the
full prompt again (e.g. user 42 on 2026-04-18 06:43:16 and 06:45:58).

## What changed

`bot.py`

- `build_system` now returns two text blocks, each with `cache_control: ephemeral`, in
  prefix order:
  1. `INSTRUCTIONS` + `profile_context(a)`: name, id, sport, zones, goal, language. These
     change only when the profile file is edited, never on `save_fact`, and no date
     is in them. Byte-identical across days and across memory writes for one athlete.
  2. `volatile_context(a, today)`: today's date and the long-term facts. This is the only
     part a `save_fact` touches.
- `athlete_context` was split into `profile_context` and `volatile_context`. Nothing else
  in the file used it.
- Moving the profile into block 1 is deliberate, not cosmetic (see the open item below).

`README.md`: the caching paragraph now describes the two blocks.

Tests (run outside the repo with a fake LLM and temp data/log paths; the repo's `data/`
and `logs/` were not touched):

- two blocks, both with markers; facts and date only in block 2;
- block 1 is unchanged after `save_fact` and after a day change; block 2 changes after `save_fact`;
- a full `reply()` loop where round 1 calls `save_fact`: round 2 sends the same block 1
  bytes and the new fact appears only in block 2.

All pass. The tests do not call the API, so they show the request structure is right,
not the billing effect.

## Open item: the 1024-token minimum (not fixed yet)

Anthropic ignores a `cache_control` marker when the cached prefix is shorter than the
model's minimum. For Sonnet 4.5 that is 1024 tokens, and the prefix counts tools as well
as system text. No tokenizer or API key is available here, so I estimated from the logs.
The logged 1046-token cache on 2026-04-18 (core tools + instructions + Marta's tail) gives
about 0.33 tokens per character.

- The `save_fact` path sends only the two core tools. The block-1 prefix there is
  estimated at **≈995 tokens**, which is under 1024 by a margin about the size of my error.
  It may or may not be cached.
- Adding the `plan` group gives ≈1062, and the `race` group would be about the same. Those
  calls are probably above the minimum.

Why it matters: if block 1 is under the minimum, the marker is silently dropped, and the
split does nothing on the `save_fact` path. The colleague's ~780-token static block would
have hit the same problem: their note does not mention the minimum.

The fix that is certain to clear it is to always send all tool definitions (core + plan +
race ≈ 1140 tokens). That also stops keyword-driven tool changes from changing the prefix
(see below). I did **not** do it, because `NOTES.md` says to keep the keyword tool filter.
Please decide.

Check after deploying (from `logs/usage.jsonl`):

- A `save_fact` round-2 call should show `cache_read_input_tokens` ≈ 995 (block 1) and a
  small `cache_creation_input_tokens` (≈ 50–70, block 2). That means it works.
- If it still shows `cache_read: 0` and `cache_creation` ≈ the whole prompt (~1050),
  block 1 is under the minimum. Then do the always-send-all-tools change above.

## Colleague's note: what applied here

Applied:

- Two `cache_control` blocks, static instructions first, volatile facts and date last,
  so a memory write only touches the last block.
- Keep the full fact list in the prompt. Did not add top-N fact selection; that would
  change the tail on every message.
- Diagnose with `cache_creation_input_tokens` / `cache_read_input_tokens`.

Did not apply, or applied differently:

- Their sizes (780 static / 240 tail) do not match this bot. Measured estimates here: static
  instructions + core tools ≈ 946 tokens before the profile move, tail ≈ 50–100 tokens.
- The minimum-length constraint (above) was not in their note and matters here.
- Their tool-group trap applies in full. Tools sit before the system prompt in the prefix,
  so a keyword match that adds a tool group changes the whole prefix. The log shows it:
  the `plan_week` call at 06:44:31 wrote 1305 tokens with `cache_read: 0`, and the
  `predict_race` call at 08:03:24 wrote 1334. This is separate from the memory-write
  problem, and I left the filter alone as NOTES asks.
- Their "byte stability in the tools array" point: the tools are unchanged by this edit.
  The stability problem only comes from keyword-driven tool sets, as above.

## Not changed

- No API calls, no deploy, nothing committed. The working tree has `bot.py`, `README.md`,
  and this file.
- `data/athletes.json` and `logs/usage.jsonl` are untouched.
