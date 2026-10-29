# Fix: a save_fact no longer evicts the cached system prompt

## Why it happened
The whole system prompt (instructions + athlete context) was one text block with one
`cache_control` marker. Cache hits are matched on whole content blocks, so appending a
fact changed that single block and nothing before it was a cached prefix. The round right
after every `save_fact` paid a full cache write of ~1000 tokens (`logs/usage.jsonl`: round 2
after `save_fact` shows `cache_read_input_tokens: 0`, `cache_creation_input_tokens` ~1050).
The facts also sat in the middle of the context (with `Language:` after them), so appends
weren't even at the end of the text.

## What I changed (`bot.py`, `build_system` / `athlete_profile`)
The system prompt is now an append-only list of blocks:

1. `INSTRUCTIONS` (static)
2. the athlete profile: date, name/sport, zones, goal, language, and the "Long-term facts" header
3. one block per fact (`- ...`), in insertion order

`cache_control` sits on the **last** block. When `save_fact` appends a fact, the old prefix
is still unchanged, block for block. The API checks earlier block boundaries before the
breakpoint (lookback, about 20 blocks), so it finds the entry the previous request wrote
at the old last block. It reads that from cache and writes only the new fact (~15 tokens),
not the whole prompt again. The "(none yet)" placeholder is gone, because a placeholder
block that gets replaced by the first fact would break the prefix. The header says the
list may be empty instead.

I did not just add a second breakpoint after `INSTRUCTIONS`. Going by the logs (user 77's
first write with no facts was 1024 tokens in total), core tools + instructions come to
roughly 950 tokens. That is under Sonnet 4.5's 1024-token minimum for a cacheable prefix,
so that breakpoint would silently do nothing. The append-only layout doesn't depend on
the static part reaching the minimum.

`README.md`: updated the sentence about prompt caching to describe the new layout.

## Checked
I could not make a live API call (no key, no external calls). I ran an offline
simulation with a fake LLM that applies block-level prefix caching with lookback
(script kept outside the repo). It runs `reply()` for user 77: plain message → save_fact →
plain → save_fact. After the first message, every call reads the existing prefix from
cache. The round after `save_fact` writes 1 new block, and the next message writes nothing.
Before this change, each of those rounds rewrote the full prompt. Please confirm in
`logs/usage.jsonl` after deploying: round 2 after `save_fact` should show
`cache_read_input_tokens` ≈ the previous total and `cache_creation_input_tokens` ≈ 15–20.

## Rules to keep it working
- Facts must stay the last system blocks and in insertion order. Editing, reordering or
  deleting a fact invalidates the prefix from that point on (a one-off write, which is fine).
- Don't put anything that changes per message into the system blocks. The date changes
  once a day, which doesn't matter with a 5-minute TTL.

## Not changed (known remaining misses)
- Tools come before the system prompt in the cached prefix. A message that adds the `plan`
  or `race` tool group therefore misses the cache and writes its own entry (e.g. the
  1305/1334-token writes in the log). The next plain message still hits the core-tools entry. That cost comes from the keyword tool
  filtering, which NOTES.md says to keep, so I left it. If it ever matters, always sending
  every tool in a fixed order would remove those misses but cost more tool tokens per call.
