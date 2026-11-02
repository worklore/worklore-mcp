# Fix: memory writes no longer evict the static system prompt

## Cause
`build_system()` sent the whole system prompt as one text block with one
`cache_control` marker. The cache is a prefix hash over tools → system → messages,
so when `save_fact` appended a fact (near the end of that block), the hash at the
only breakpoint changed and the whole ~1000-token prompt, including the
instructions that never change, was written again (`cache_read_input_tokens: 0`,
`cache_creation_input_tokens` ≈ the full prompt in `logs/usage.jsonl`).

## Change (`bot.py`)
- `athlete_context()` is split into two parts:
  - `athlete_profile(a)`: name/id, sport, zones, goal, language. `save_fact`
    never touches these and they don't change by date.
  - `athlete_memory(a, today)`: today's date + long-term facts, the part that changes.
- `build_system()` now returns **two** text blocks, each with
  `cache_control: {"type": "ephemeral"}`:
  1. `INSTRUCTIONS` + profile: stays byte-identical across memory writes and days.
  2. date + facts: the only part re-cached after a `save_fact`.
- Two of the four allowed breakpoints are used. Tool filtering is unchanged (NOTES.md
  says to keep it). Within one message the tool list is fixed, so loop rounds still hit.
- Checked locally: for athlete 42, block 1 is identical before and after adding a
  fact and moving the date forward a day; block 2 differs.
- README's caching paragraph was updated to match.

## Why the profile goes in segment 1 (not just the instructions)
Sonnet 4.5 won't cache a prefix under **1024 tokens**, and a marker below that
size caches nothing without any error. From the logs, a new athlete with no facts
caches exactly 1024 tokens for tools + the whole system prompt. That puts tools +
`INSTRUCTIONS` alone at about 950–980 tokens, which is probably *under* the
minimum. A split with only the instructions in segment 1 would most likely have
changed nothing. Adding the stable profile (~50 tokens) brings segment 1 to about
the threshold. That's an estimate: I had no tokenizer and made no API calls. The date
also moved out of segment 1 so a day change doesn't evict it.

## How to verify (from `logs/usage.jsonl`)
After a `save_fact`, the next round should show `cache_read_input_tokens` ≈ segment 1
(~1000) and `cache_creation_input_tokens` ≈ only the date+facts tail (tens of tokens),
not ~1000 written again.
If the read is still 0, segment 1 is under the 1024-token minimum. Fix it by adding
more stable content to segment 1 (e.g. send all tool groups always, or grow the
instructions). Never put the date or facts in it.

Messages that pull in a tool group (plan/race) still write a separate cache entry
once, because tools come before the system prompt. That's unrelated to memory and
left as is.
