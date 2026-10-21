# Prompt cache fix

`bot.py` now sends two cached system text blocks. The first contains the fixed coaching instructions and fixed guidance; the second contains the date, athlete profile, zones, goal, facts and language. After `save_fact`, the next request changes only the second block, so Claude can reuse the static prefix and create a new cache entry for the athlete tail.

The old full prompt was only 1,024–1,046 cached tokens in the supplied usage log. Splitting it without adding fixed content risked putting the first breakpoint below Claude's 1,024-token cache minimum. I added 180 words of athlete-independent coaching guidance to make that prefix eligible. The core tool definitions stay in their existing order ahead of the system blocks.

## What applied from the colleague's note

- Applied: two `cache_control: ephemeral` breakpoints, with a byte-stable first block and a changing athlete block.
- Applied: keep the existing tool selection and ordering stable during each tool loop. Different tool groups can still produce a different cache prefix between messages.
- Applied: retain all saved facts in the athlete block. Selecting different facts per message would make that block harder to reuse.
- Already present: every API response logs `cache_creation_input_tokens` and `cache_read_input_tokens` in `logs/usage.jsonl`; no logging change was needed.
- Not applied: the note's earlier tool-filtering change. This repo already filters tools by keyword, and `NOTES.md` says to leave it in place.

## Verification

`python3 -m py_compile bot.py` and `git diff --check` passed. A local fake-LLM tool-loop check called `save_fact` and confirmed that the next request includes the new fact, keeps the first system block and tool list identical, and logs both rounds. A live cache hit was not measured because the Anthropic SDK is not installed here. The expected live check is a `save_fact` round followed by a request within the cache TTL: `cache_read_input_tokens` should remain nonzero for the fixed prefix, while `cache_creation_input_tokens` should cover only the changed tail.
