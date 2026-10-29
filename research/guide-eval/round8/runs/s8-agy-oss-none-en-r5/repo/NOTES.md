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
