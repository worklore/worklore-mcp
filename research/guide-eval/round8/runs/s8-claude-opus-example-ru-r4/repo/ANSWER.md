# The cache stays warm after `save_fact`

## What was wrong

`build_system()` put everything into one text block with one `cache_control`:
instructions + date + profile + facts. The cache works on prefixes, so a new fact
changed the block and invalidated the whole cached prefix. In `logs/usage.jsonl`, the
call right after every `save_fact` shows `cache_read_input_tokens: 0` and
`cache_creation_input_tokens` ≈ 1040–1100. That's the whole prompt again, at the write
price (×1.25).

## Why the colleague's fix alone isn't enough here

The colleague used two markers: [static instructions] + [whole volatile tail]. For this
bot, that layout doesn't work. Sonnet 4.5 caches only a prefix of at least 1024 tokens,
and anything shorter is silently skipped. The logs give the size: the first message from
user 77 cost exactly `cache_creation_input_tokens: 1024` for the whole prompt, and each
fact adds ~15 tokens. So core tools + instructions come to ~920–950 tokens, under the
minimum. A marker after the instructions would never write a cache entry, and a
rewritten tail would still cost the whole prompt.
`tests/test_cache_layout.py::test_two_segments_alone_hit_the_minimum` checks this.

## What I changed (`bot.py`, `build_system` / `athlete_context`)

The system prompt is now a list of blocks:

1. `INSTRUCTIONS`: byte-identical for all athletes and days, with its own
   `cache_control`.
2. Athlete context: date, profile, zones, goal, language, and the header
   `Long-term facts (oldest first):`. I moved the language line above the facts so it
   doesn't sit after the part that changes.
3. One block per fact, `- <fact>`. `cache_control` goes on the last block.

`save_fact` only appends a fact (`a.facts.append`), so the new request differs from the
previous one by exactly one block at the end. The API checks earlier block boundaries
(lookback up to ~20 blocks before a breakpoint), finds the previous request's cache
entry one block back, and reads it. Only the new fact is written, ~15 tokens instead of
~1050. This holds both for the second round of the tool loop (where the fact is already
in the prompt) and for the next message. Uses 2 markers out of the 4 allowed.

Constraint, also written in the code comment: facts must stay append-only. Editing,
deleting, deduplicating or reordering old facts (for example top-N by relevance) breaks
the prefix from the changed fact onward. The `(none yet)` placeholder is gone, because
the first fact would have replaced it.

I left tool filtering alone, as `NOTES.md` asks.

Also: README updated; added `tests/test_cache_layout.py`. It makes no API calls. It
checks the block structure and replays a "message → save_fact → message → save_fact →
message" scenario against a simplified prefix-cache model, with token counts calibrated
to `usage.jsonl`:

```
old layout:  after save_fact (0 read, 1039 created), (0, 1051)
new layout:  after save_fact (1026 read, 11 created), (1037, 12)
```

Run it with `python3 -m unittest discover tests`. All 5 tests pass. It's a model, not the
real API. I didn't run the bot against Anthropic (no key, and external calls were off
limits).

## How to check in production

In `logs/usage.jsonl`, the call after `save_fact` (round 2 and the next message) should
show `cache_read_input_tokens` ≈ the size of the previous prompt and
`cache_creation_input_tokens` ≈ 10–30. If it shows 0 / ~1000 again, something has made
the prefix stop being byte-stable (a changed profile, a value inserted into the
instructions, an edited old fact).

## Which parts of the colleague's note helped

- **Helped:** the diagnosis (prefix hash: a memory write invalidates everything after
  it), separating the byte-stable instructions into their own block with their own
  marker, the rule "no top-N selection of facts, load them all, in a stable order"
  (here it's even stricter: append-only), the tip to keep tools above the system prompt
  stable, and the check through `cache_creation_input_tokens` / `cache_read_input_tokens`.
- **Didn't carry over as is:** the two-segment layout itself. In their case the static
  part was bigger, and here it's under the 1024-token minimum. So the second segment is
  split into a block per fact, and the cache is kept by lookback rather than by the
  instructions marker. The instructions marker only helps here when an extra tool group
  is in the request (the prefix grows past 1024 and becomes shared by all athletes).
- **Skipped:** keyword tool filtering. It's already in the bot (`select_tools`), and
  `NOTES.md` asks to leave it.
