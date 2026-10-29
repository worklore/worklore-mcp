# Fix: save_fact no longer evicts the cached system prompt

## What was wrong

`build_system` returned one text block (instructions + athlete context with the facts
in the middle) with one `cache_control` marker. Prompt caching hashes the prefix at
block boundaries, so appending a fact changed the only block and nothing matched. The
call after every `save_fact` (round 2 of the same tool loop, since `run_tool` mutates
`a.facts` and the system prompt is rebuilt each round) paid full creation. In
`logs/usage.jsonl` all 6 `save_fact`s are followed by `cache_read_input_tokens: 0`,
`cache_creation_input_tokens` 1039–1104.

## What I changed

`bot.py`, `build_system` / `athlete_context`: the system prompt is now a list of blocks:

1. `INSTRUCTIONS`, byte-identical for every athlete and day, marked `cache_control`.
2. Athlete context: date, name, sport, zones, goal, language, and a "Long-term facts"
   header. `Language` moved above the facts so nothing comes after them.
3. One text block per fact, oldest first. The last block (or block 2 if there are no
   facts) is marked `cache_control`.

A `save_fact` now only **appends** a block. On the next call the API looks back over
earlier block boundaries (up to ~20) and finds the entry the previous call wrote at the
old last fact. So it reads the whole old prompt and writes only the new fact
(~13–15 tokens; in the logs each fact adds 14–15). That's the same mechanism as
moving the marker forward in a multi-turn conversation. Tool rounds and follow-ups
behave as before. Two markers are used, under the limit of 4.

I also added `tests/test_cache_layout.py`, an offline test with no API key and no
network. Its fake client models the cache: writes at markers if the prefix is at least
1024 tokens, lookups with a 20-block lookback, token counts calibrated so athlete 42
comes to 1046 as in the log. Results for athlete 42: a message, then one with a
`save_fact`, then a follow-up:

| call | old layout (read / create) | new layout (read / create) |
|---|---|---|
| msg 1 | 0 / 1046 | 0 / 1046 |
| msg 2 round 1 (save_fact) | 1046 / 0 | 1046 / 0 |
| msg 2 round 2, after the write | **0 / 1061** | **1046 / 13** |
| msg 3 | 1061 / 0 | 1059 / 0 |

The old `bot.py` fails both tests and the new one passes. README updated to match.

## The colleague's note: what applied and what didn't

- **Applied: the diagnosis.** One marker at the end of a system prompt that contains
  memory means every memory write changes the prefix hash and evicts everything.
  That's exactly what happened here.
- **Applied: keeping the instructions byte-stable and in their own block with their own
  marker** (step 1, first half). `INSTRUCTIONS` had no interpolated values, so nothing
  needed to be hunted down.
- **Did not work as written here: "two markers, instructions | volatile tail" as the
  whole fix.** A marker only creates a cache entry if the prefix up to it reaches the
  model's minimum cacheable length. That's 1024 tokens for `claude-sonnet-4-5`. The note's
  static block was ~780 tokens. Here, tools + tool-use overhead + instructions come to
  about 930 tokens: the whole prompt is 1046 with 3 facts, and the tail is clearly over
  ~100. So with only the core tools, the instruction marker is silently ignored. A
  memory write would still miss everything, and the fake confirms it: the two-marker
  variant gets 0 read after the write. The fix that works independent of that threshold
  is giving each fact its own block and relying on the lookback. I kept the instruction
  marker anyway. It costs nothing and starts paying off whenever tools + instructions
  reach 1024 tokens: when the plan/race group is attached (~+245 tokens), if the
  instructions grow, or on a model with a lower minimum. Then other athletes and the
  first message of a new day can reuse it.
- **Applied: "don't select top-N facts per message."** Facts stay all-included and in a
  stable order. I added one constraint of my own: facts must stay **append-only**.
  Editing, deduplicating, or reordering one re-caches from that fact onward (still only
  the tail).
- **Applied as advice only: keep tools stable / don't filter aggressively.** `NOTES.md` says
  to keep the keyword tool filtering, so I didn't touch it. A message that adds a tool
  group still re-caches once (e.g. 1305 at 06:44:31), as the note describes.
- **Applied: read `usage`.** `log_usage` already logs all the fields needed. The table above
  is what the next real `logs/usage.jsonl` should look like.
- **Not applicable:** MCP and the ~55-tool schema filtering (this bot has 4 tools), Telegram
  details, and the "order the tail rarest-changing first, it's one hash anyway" advice. Here
  the tail is no longer one hash. Its order matters: the date/profile block goes before the
  facts, and facts must be last.

## Caveats

- Token counts in the test are estimates (chars/4 plus a calibrated tool overhead), not
  API counts. Nothing was sent to the API. To verify for real, run two messages and then
  a `save_fact` message within 5 minutes and check that round 2 after the write shows
  `cache_read_input_tokens` ≈ the previous prompt and `cache_creation_input_tokens` ≈
  15–30.
- This existed before and isn't fixed: a new athlete with 0–1 short facts can have a whole
  prompt under 1024 tokens, which then isn't cached at all (Jonas with 2 facts sits at
  exactly 1024). If that matters, the instructions or the always-on tool set would need
  to grow. I didn't pad the prompt.
- The date sits in block 2, so the first message of each day re-caches the athlete tail
  once. That's unavoidable while the date is in the system prompt, and cheap.
