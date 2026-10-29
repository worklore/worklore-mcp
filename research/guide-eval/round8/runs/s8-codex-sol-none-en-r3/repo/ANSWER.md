# Prompt cache fix

The old `build_system()` put coaching instructions, athlete details, and every
long-term fact into one cached text block. `save_fact` changed that block, so the
next API call wrote the entire prompt to cache again. The usage log shows this
as `cache_read_input_tokens: 0` after memory writes.

I split the system prompt into a stable base block (instructions and profile)
and one block per saved fact. The base always has a cache breakpoint. When facts
exist, the newest fact has a second breakpoint. A `save_fact` now appends a block
after the previously cached prefix, allowing the next tool round and later
messages to reuse the earlier instructions and facts. The empty-facts label sits
after the base breakpoint, so the first fact leaves the base prefix unchanged.
I expanded the stable instructions with guidance on using athlete records to
clear this model's 1,024-token minimum cacheable prefix, based on the token
counts in the existing log. Tool selection is unchanged.

Verified locally with `python3 -m unittest -v` (2 tests),
`python3 -m py_compile bot.py test_bot.py`, and `git diff --check`. The tests
check that a saved fact appears in the next tool round and later requests while
the earlier system blocks retain their text and breakpoints. No live Claude API
call was made, so actual cache-read usage has not been measured. Cache entries
still expire after five minutes; changing the selected tool definitions or the
date can require a fresh cache write.
