# Fix: a `save_fact` write no longer evicts the static instructions

## Cause

`build_system()` returned one text block containing `INSTRUCTIONS` plus
`athlete_context()` (date, profile, zones, goal, facts, language), with a single
`cache_control` marker at the end. The prompt cache is a prefix hash, so any byte
change inside that block misses the whole block. Every `save_fact` rewrites the
facts list, which changes the block, which re-caches the ~1000 tokens of
instructions too. That matches `logs/usage.jsonl` and `NOTES.md`: the call right
after a `save_fact` has `cache_read_input_tokens: 0` and a full
`cache_creation_input_tokens`.

## Change (`bot.py`, `build_system`)

The system prompt is now two text blocks, each with `cache_control: ephemeral`:

1. `INSTRUCTIONS`, unmodified text. It contains no interpolated values, so it is
   byte-identical across athletes, days and memory writes.
2. `athlete_context(a, today)`: everything per-athlete and volatile.

A memory write changes only block 2. Block 1 stays cached. Two of Anthropic's
four allowed markers are used. `build_request`, `select_tools`, the tools array
and the message loop are unchanged.

`README.md` (the caching paragraph) is updated to describe the two blocks.

## Verification done

- Ran `build_system` in a local script: block 1 is identical for two athletes,
  for a different date, and after a `save_fact` (`assert` passed). Block 2
  changes on a date change and on a memory write. Both blocks carry the
  ephemeral marker.
- The module imports and compiles without the SDK installed.

**Not verified:** no real API call was made. There is no key in this session, and
a live call costs money and is outward-facing, so I did not make one. The check
that settles it is the one in the colleague note: after a `save_fact`, the next
call should show `cache_read_input_tokens` covering block 1 and
`cache_creation_input_tokens` near the size of block 2 only (~60 tokens of
context plus the date line). If `cache_creation` is still about the whole prompt,
see the caveat below.

## Caveats (please read)

1. **Minimum cacheable size.** The API only caches a prefix of at least 1024 tokens
   for Sonnet (`claude-sonnet-4-5`). The prefix up to block 1 is the tools array
   plus `INSTRUCTIONS`. Calibrating against the logged numbers (the old
   single-block request was 1046 tokens for 3111 characters, about 3 characters
   per token), a simple message with only the two core tools comes to roughly
   980 tokens. In that case the block-1 marker is silently ignored and block 2's
   marker caches the whole prefix, which is the old behaviour. Messages that
   also pull in the `plan` or `race` tool group are larger and should clear the
   minimum, but that is borderline by my estimate. This needs the real `usage`
   numbers to confirm. I did not pad the prompt to get over the minimum, because
   that would be adding content to the coaching instructions, which is your call.
   Options if the check fails: add real static content (for example, fuller
   coaching rules), or always send the full tool set (costs more tokens on simple
   messages, the trade the keyword filter was made to avoid).

2. **Tool filtering still shares the prefix.** The tools array sits above the
   system prompt, so a message that contains `plan`, `race` and similar words
   changes the tools prefix and misses block 1 as well. Within one message's tool
   loop the tools are constant, so this only costs once per such message. It is
   not a memory-write problem, so I left it alone.

3. **Date is in block 2.** Block 2 changes once per day as well as on memory
   writes. That is intended: the tail is small (~60 tokens).

## Colleague note: what applied

- **Applied:** two `cache_control: ephemeral` markers, one static block and one
  volatile tail. A memory write re-caches only the tail. Static block kept
  byte-stable (no interpolated values). Verify steps adapted to usage fields.
- **Applied as a principle, nothing to change:** the tools array and everything
  above the system prompt should stay byte-stable. The tool groups are in a fixed
  order, and the tools are not reordered. The filter itself is unchanged (caveat 2).
- **Applied as a check:** the per-message selection warning. This code has no
  top-N fact selection. All facts are always loaded, so the tail is not
  personalised per message.
- **Not applied:** "rarest-changing first" ordering inside block 2. Within one
  cache entry, order doesn't change what gets evicted, so I kept the existing
  field order. Splitting block 2 further would use more markers for little gain.
- **Not applicable:** the Telegram details, the coach-bot content, and the
  specific token counts. Those are that project's numbers, not this one's.
