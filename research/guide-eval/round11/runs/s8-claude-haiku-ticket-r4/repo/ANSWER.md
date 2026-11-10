# Answer: a memory write should not evict the static instructions

## Cause

`build_system()` in `bot.py` returned one text block: `INSTRUCTIONS` plus the
per-athlete context (date, profile, zones, goal, facts, language), with a single
`cache_control` marker at the end. Caching is prefix-based, so any change inside
that block misses the cache for the whole block. `save_fact` appends to
`athlete.facts`, which changes the block, so every write re-created the full
prompt. `logs/usage.jsonl` shows it: the call after each `save_fact` has
`cache_read_input_tokens: 0` and `cache_creation_input_tokens` close to the full
prompt size.

## Change

`bot.py`, `build_system()`: the system prompt is now two text blocks, each with
its own `cache_control: {"type": "ephemeral"}` marker.

1. `INSTRUCTIONS`: the coaching rules. This text is the same for every athlete and
   every day, with no interpolated values. A `save_fact` write leaves it untouched,
   so it stays cached.
2. `athlete_context(a, today)`: the per-athlete tail. It is re-cached only when its
   own bytes change: a `save_fact`, a new day, or a profile edit.

Nothing else in the request changed: the tool list, the facts (all of them are
still loaded), and the message loop are the same. `README.md` has a sentence on
caching that now describes the two blocks.

## Verification

I checked this offline. No API calls were made, and the real `data/` and `logs/`
were not touched. I used a fake LLM and temp files for a `reply()` run where round 1
calls `save_fact` and round 2 answers:

- The system prompt has 2 cache breakpoints.
- Block 1 is byte-identical between round 1 and round 2 (the `save_fact` round).
- Block 2 changes after the write and contains the new fact.
- Block 1 is identical across different athletes and dates.
- The tool list is identical across rounds.

## Not verified: the 1024-token minimum

I could not measure token counts here. The static block is about 2,480 characters.
That is roughly 750–800 tokens by the usage rows, and the cache-eligible prefix also
includes the tool definitions, which sit before the system prompt. For Sonnet, a
cache breakpoint is only honoured if the prefix up to it is at least 1024 tokens.
For a message that uses only the core tools, block 1 may fall below that. The API
then ignores that marker without an error. Block 2's marker still caches the full
prefix, so the change is never worse than before, but the saving only shows up
when block 1 clears the minimum.

To check after deploying, look at `logs/usage.jsonl`:

- A `save_fact` round should show `cache_creation_input_tokens` near the size of
  the tail (about 60–100 tokens), not about 1,000.
- Follow-up calls should show `cache_read_input_tokens` near 1,000 or more.
- If `cache_read_input_tokens` stays 0 on every call, block 1 is below the minimum.
  The fix is to pad the static prefix above 1024 tokens or to put a stable tool
  list above it. Both are trade-offs, so I did not make them without your input.

## What applied from the colleague's note

- **Split `system` into two cache-marked text blocks, static first.** Applied; this
  is the main change.
- **Static block with no interpolated date, name or counter.** Applied; `INSTRUCTIONS`
  is a constant, and the test checks it.
- **Keep loading all facts, no per-message top-N selection.** Applied; nothing
  changed. Selecting facts per message would change the tail on every message.
- **Two of the four allowed markers.** Applied; the request uses two.
- **Monitor `cache_creation` and `cache_read` in the usage log.** Applied as the
  check above.
- **Tool groups sit above the system prompt, so a group change re-caches
  everything.** This applies, but I did not change it. `NOTES.md` records the
  keyword tool filter as a clear win (about 75% fewer tool tokens on short
  messages). A group change between messages still evicts the cache, but within a
  message's tool loop the tool list is constant, which is where caching helps most.
- **Keep the tools array byte-stable.** Applies and already holds: `select_tools()`
  returns core tools, then the groups, in a fixed order.
- **Put the rarest-changing content first inside the tail.** Not changed. The tail is
  one block, and its internal order does not affect caching beyond the tail, which
  is small.
- **The colleague's token counts (~780 and ~240).** Not used. They come from a
  different prompt; I did not measure these numbers.
