# Why save_fact evicted the system prompt, and what changed

## Diagnosis

`build_system` sent instructions, profile, date and facts as **one** cached text block.
Prompt caching matches on the prefix, so when `save_fact` appended a fact, the block
changed and the cache missed. That happened as early as round 2 of the same tool loop,
because `run_tool` mutates the athlete record and the loop rebuilt the system prompt
every round. In `logs/usage.jsonl`, every call right after a `save_fact` shows
`cache_read_input_tokens: 0` and `cache_creation_input_tokens` of about 1040–1100.

## Why splitting into two segments isn't enough here

The colleague's main fix is two `cache_control` segments: static instructions first,
then a volatile per-user tail. On this bot, that alone would probably do nothing.

- The model is `claude-sonnet-4-5`, and its **minimum cacheable prefix is 1024 tokens**.
  Smaller prefixes are silently not cached, even if they have a marker.
- The log shows how close this bot is to that limit. User 77's whole prefix (tools +
  instructions + profile + 2 facts) is cached at exactly **1024** tokens. Each fact
  adds about 15 tokens, so tools + instructions come to roughly **900 tokens**.
- A segment holding only the instructions would therefore fall below the minimum
  with the core tool set. Its marker would be ignored, and every `save_fact` would
  still rebuild about 1050 tokens. (The colleague's static block probably cleared the
  minimum because ~55 tool schemas came before it. Here only 2 core tools do.)

The only cacheable prefix is one that **includes the per-athlete block**. So that
block has to stay byte-stable across memory writes.

## What changed (bot.py)

1. **Facts are snapshotted.** `Athlete` has two new fields: `cached_facts`, the
   number of facts in the cached block, and `last_call`. `athlete_context()` lists
   only `facts[:cached_facts]`.
2. **New facts go in an uncached tail.** `build_system()` now returns
   `[instructions ✓cache, profile+language+date+fact snapshot ✓cache, recent facts (no marker)]`.
   A `save_fact` only adds about 15 tokens to the unmarked third block. No cached
   byte changes, so the next call reads the whole ~1050-token prefix from cache. The
   recent facts are still in the prompt, so rule 16 ("don't re-save a known fact")
   keeps working.
3. **Recent facts move into the snapshot only when the cache is cold anyway**
   (`snapshot_facts()`): no call in the last 5 minutes, or a new day (the "Today" line
   changes the block that day anyway). Rebuilding the snapshot then costs nothing extra.
   `last_call` is recorded after each response, so the code errs toward not
   rebuilding. A wrong guess only costs a few uncached fact tokens.
4. **The system prompt is built once per message**, not once per loop round. The fact
   saved in round 1 is already visible to the model as its own tool call, so round 2
   reuses identical blocks.
5. Marker 1 (instructions only) is kept. It does nothing with core tools only, because
   it's under 1024 tokens. With a plan or race tool group attached it clears the
   minimum and is shared across users. It costs nothing when it's ignored.
6. `reply()` saves the athlete at the end to persist `last_call`/`cached_facts`.
   Existing records without these fields load with defaults and rebuild on first use.

Other changes:
- The "Language" line moved from the bottom of the context block up next to the profile.
- `build_request()` now takes the prebuilt system blocks.
- README updated.

## Expected effect

| Call | Before | After |
|---|---|---|
| Round 2 after a `save_fact` | create ~1050 | read ~1050 |
| Next message (within 5 min) | read | read ~1050, +~15 uncached per new fact |
| First message after cache expiry | create | create (unchanged; recent facts get folded in here) |

**Not verified against the real API.** The SDK isn't installed here, and I made no
external calls. Instead, I ran a fake-LLM simulation (temporary files, deleted
afterwards) through three messages, one of which included a `save_fact`. The cached
blocks were byte-identical across all four API calls, and the new fact appeared in
the uncached tail. After faking a 6-minute gap, the fact moved into the cached block.

To check against the real API: send a message, then one that triggers `save_fact`,
then another, all within 5 minutes. Rounds after the save should show
`cache_creation_input_tokens: 0` and `cache_read` of about 1050.

## Which parts of the colleague's note applied

- **Applied:** The diagnosis (a prefix hash covering instructions and memory, so one
  fact evicts everything).
- **Applied:** "Read `usage` to see what happened". That is how the 1024-token limit
  showed up.
- **Applied:** Keeping cached blocks byte-stable, with no interpolated values in the
  instructions. `INSTRUCTIONS` was already a plain constant.
- **Applied:** Within one message's tool loop, keep everything constant. That is why
  I freeze the system prompt per message.
- **Applied in part:** Two `cache_control` markers. I kept them, but they are not what
  fixes this case (see above). The fix is an append-only uncached tail with a deferred
  snapshot rebuild.
- **Applied:** Rejecting top-N or per-message fact selection. Nothing here selects
  facts per message.
- **Did not apply:** "~780-token static block caches on its own". It doesn't on Sonnet
  4.5 with 2 core tools, because it's under the 1024 minimum.
- **Left alone:** Tool filtering. NOTES.md says to keep it. Its cost is still visible:
  a message that adds the plan or race group misses the whole prefix (the 1305/1334
  creations in the log). Sending all tools all the time would remove those misses
  and push marker 1 over the minimum. That trade-off is the owner's decision, so I
  only mention it.
- **Not relevant:** MCP, Telegram transport, the 4-marker limit (we use 2).
