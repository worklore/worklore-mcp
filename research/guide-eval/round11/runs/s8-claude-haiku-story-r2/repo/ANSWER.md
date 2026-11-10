# Fix: a memory write no longer evicts the static instructions

## Cause

`build_system()` in `bot.py` put the instructions and the per-athlete context
(date, profile, zones, goal, facts, language) into one text block with one
`cache_control: ephemeral` marker. The cache is a prefix hash, so any change
to the facts changed the hash of the whole block. Every `save_fact` therefore
evicted the instructions too. That matches `logs/usage.jsonl`: the call right
after a save shows `cache_read_input_tokens: 0` and `cache_creation_input_tokens`
about the size of the full prompt.

## Change

`bot.py`, `build_system()`: the system prompt is now two text blocks, each with
its own `cache_control: {"type": "ephemeral"}` marker.

1. Block 1 is `INSTRUCTIONS`, unchanged and with no interpolated values. It is
   byte-identical for every athlete and every day.
2. Block 2 is `athlete_context(a, today)`, the volatile tail. A memory write
   changes only this block.

Nothing else changed: tools, model, `select_tools`, the tool loop and usage
logging are untouched. The tool list is built in a fixed order and does not
depend on memory, so a `save_fact` does not change anything above the system
prompt.

Expected usage after the change:
- Within the 5-minute TTL, a normal message or a tool-loop round reads both
  blocks from cache.
- A message after `save_fact` reads block 1 from cache
  (`cache_read_input_tokens` ≈ the instructions plus tools) and writes only
  block 2 (`cache_creation_input_tokens` ≈ the tail, tens of tokens for a
  typical athlete).

## Verified offline

I did not call the API: there is no key in this environment. I checked the
request layout by calling `build_system()` directly:

- Two blocks, each with `cache_control`.
- Block 1 is byte-identical across different athletes and different dates.
- Block 1 is byte-identical after a `save_fact`-style change to facts.
- Block 2 changes after a fact is added.
- Block 1 contains no date or name.
- `select_tools()` returns the same list for the same message.

Approximate size (chars/4): block 1 about 620 tokens, block 2 about 50 tokens
for one athlete with one fact. The tail grows with the number of facts.

## Still to check against the live API

- **Minimum cacheable length.** Sonnet-class models only cache a prefix of at
  least about 1024 tokens. The breakpoint-1 prefix is tools plus instructions,
  which is probably just above that, but I could not confirm it. If it is
  below, the marker on block 1 is silently ignored and the tools plus
  instructions are cached only through block 2. Memory writes would then evict
  them again. Check: the first call after a `save_fact` should show
  `cache_read_input_tokens` ≈ tools + instructions. If it shows 0 and
  `cache_creation` ≈ the full prompt, the prefix is under the minimum.
- **Tool-group changes.** A message that adds a tool group (plan or race
  keywords) changes the tools, which sit above the system prompt. That evicts
  both blocks once. This is existing behaviour and it is the cost of the
  keyword filter; I did not change it.

## Colleague's note: what applied

- **Two `cache_control` markers, static instructions first, volatile tail
  second.** Applied. This is the core of the fix.
- **Block 1 must be byte-stable (no dates, names or counters).** Applied as a
  requirement. It already held; I added a comment so it stays that way.
- **Keep everything above the system prompt, especially tools, byte-stable.**
  Already true in this code. The keyword tool filter is a known exception, and
  the note accepts it.
- **Verify with `usage` (`cache_creation` and `cache_read`).** Applies, and it
  is the test to run in production. I could not run it here.
- **Do not add per-message top-N fact selection.** Does not apply: the code
  loads all facts, and I did not add any selection.
- **Reorder the tail so the rarest-changing data comes first.** Did not apply.
  The tail is one hash after the marker, so the order gives no caching benefit.
  I left it as it was.
- **Token figures (~780 static, ~240 tail).** Do not apply to these numbers.
  Here the static block is about 620 tokens and the tail about 50 tokens per
  athlete. The note's figures come from a different prompt.
- **Tool-filtering savings and the ~55-tool example.** Already in this bot
  (`TOOL_GROUPS`, about 75% fewer tool tokens per the NOTES). Nothing to change.
