# Caching fix: a save_fact no longer evicts the system prompt

## What the log actually shows

In `logs/usage.jsonl`, every `save_fact` call happens in **round 1**, and the full-prompt miss
lands in **round 2 of the same message** (e.g. 06:42:58 read 1046, then 06:43:16 created 1061
and read 0). The next message after that reads the new prompt from cache again. So there were two causes:

1. **The prompt changed mid-loop.** `reply()` rebuilt `system` from the athlete object on every
   round, and `run_tool("save_fact")` changes that same object. So round 2 sent a different prompt.
2. **A single cache marker over instructions plus athlete data.** Any change to the facts
   invalidated the whole block, including the ~2.5 KB of instructions that never change.

## What I changed (`bot.py`)

- **Build `system` once per message** in `reply()` and reuse it for every tool-loop round.
  After a save_fact, round 2 now gets a full cache hit. The model already sees the new fact in
  the tool_use/tool_result history, and it moves into the system prompt from the next message on.
- **Split `system` into blocks with stable parts first:**
  `[INSTRUCTIONS] [profile: date, name, sport, zones, goal, language, "Long-term facts:"] [fact 1] … [fact N]`
  - The instructions block has nothing interpolated into it. It is byte-identical across athletes and days.
  - `Language:` moved above the facts. Before, it came after them, so every new fact also changed the last line.
  - Each fact gets its own content block. `save_fact` only appends, so after a write the new
    request contains the old prefix ending exactly on a block boundary, which is where the
    previous request's breakpoint was. The API checks earlier block boundaries for cache hits
    (up to about 20 blocks back), so it finds that entry. **Only the new fact (~15 tokens) is
    written to the cache**, not ~1000+ tokens.
- **Three `cache_control: ephemeral` breakpoints** (the limit is 4): after the instructions,
  after the profile, and on the last fact. If a fact is ever edited or deleted instead of
  appended, or the date changes, the miss falls back to the profile or instructions breakpoint.
  The whole prompt is no longer lost.
- `build_request()` now takes the prebuilt `system`. Tool filtering is unchanged.
  The README's caching sentence is updated to match.
- Added `tests/test_caching.py`. It runs offline with a fake LLM and needs no SDK or key. It checks:
  the system prompt is identical across the rounds of one message even when save_fact runs;
  the next message is the old blocks plus one appended fact block; the breakpoints are in the
  expected places; the instructions block is identical across athletes and dates.
  Run it with `python3 tests/test_caching.py`. It passes.

## Not verified live

I had no API key and the SDK isn't installed, so this is not checked against real `usage`
numbers. To verify, send a message that triggers a save_fact and then a follow-up within 5 minutes:
- Round 2 of the save_fact message should show `cache_creation_input_tokens: 0` and read about the full prompt.
- The follow-up should read about the old prompt and create only about the size of the new fact.

## Which parts of the colleague's note applied

- **Applied: separate cache segments for the static instructions and the volatile per-user tail.**
  This is the core idea. I used three breakpoints instead of two (see below for why).
- **Applied: keep the static block byte-stable** (no dates or names in it), and **keep tool filtering**.
  `NOTES.md` also says to keep the filtering. Tools sit above `system` in the cache prefix, so a
  message that adds the plan or race group still re-caches everything once. You can see this in
  the log (1305 and 1334 creations). I left that alone, as both the note and NOTES.md suggest.
- **Applied: no top-N or per-message fact selection.** All facts are loaded every time, in
  stored order, so the tail stays cacheable.
- **Applied: check with `usage`.** The verification steps above follow the note's procedure.
- **Did not carry over as-is: "two markers fixes it".** It wouldn't be enough here, for two reasons:
  - The note's setup doesn't have the mid-loop rebuild. That bug is the actual cause of the
    round-2 misses in this log, and a second marker alone wouldn't fix it.
  - **The minimum cacheable length.** For Sonnet it's 1024 tokens, counted over the whole
    prefix up to the breakpoint, tools included. From the log, athlete 77 with 2 facts and core
    tools totals 1024 tokens. The tail is roughly 80–100 tokens, so tools + instructions come
    to roughly 930 tokens. That is likely **below the minimum**, and the API silently ignores
    breakpoints under it. So for core-tool messages, the "static" marker probably does nothing
    today. It starts working when the plan or race tools are included, or if the instructions grow.
  - That's why I added the per-fact blocks plus the last-fact breakpoint. Each cached prefix
    there is the full prompt, which is over 1024, so a fact write stays cheap even when the
    instructions-only marker is too short to count.
- **Did not apply:** the note's specific token sizes and its MCP and ~55-tool setup. This bot has 4 tools.

## Worth knowing

- If you want the instructions-only segment to cache by itself (useful across athletes and for
  the daily date change), the static prefix needs to reach 1024 tokens. One way is to always send
  the plan and race tools: about +500 tokens of tools, read at 10% price, which also removes the
  full misses when tool groups change. That conflicts with NOTES.md's "leave it", so I didn't
  do it. It's your call.
