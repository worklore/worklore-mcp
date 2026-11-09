# Notes

## 2026-04-20 — bill doubled since memory shipped

Input spend roughly doubled in the week after `save_fact` went live (2026-04-13),
with the same number of messages per day. `logs/usage.jsonl` shows it: on a normal
message the loop rounds and the next message read ~1000 tokens from cache, but
every call right after a `save_fact` has `cache_read_input_tokens: 0` and
`cache_creation_input_tokens` ~1000 again. Athletes tell the bot things about
themselves a lot in their first week, so this happens several times per chat.

Tried: shorter facts (no change), capping facts at 20 (no change, the number of
facts is not the problem). Tool filtering by keyword is from March and was a clear
win (~75% fewer tool tokens on short messages); leave it.

## 2026-11-09 — fixed: system prompt split into two cache blocks

Root cause was the single cache block mixing static instructions with the facts
list, plus the system being rebuilt every tool-loop round. `build_system` now emits
two marked blocks (instructions + profile header | date + facts) and `reply`
snapshotted the system once per message, so a memory write never changes the
request prefix mid-loop. See ANSWER.md. One open caveat: block 1 is near
Anthropic's 1024-token minimum cacheable prefix for claude-sonnet-4-5; if it falls
short the design degrades to the old single-block behavior rather than below it.
Worth confirming `cache_read_input_tokens` stays high on the next real bill.
