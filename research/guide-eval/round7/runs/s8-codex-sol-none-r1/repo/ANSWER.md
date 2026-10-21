# Prompt cache fix

`build_system()` now sends two system blocks. The first contains only the coaching instructions and has the `cache_control` marker. The second contains the current date and athlete details, including long-term facts, without a marker. A `save_fact` therefore changes only the uncached suffix on the next tool round and on later messages; the marked prefix stays byte-for-byte the same.

I added clarifications of the existing coaching rules to the stable block. The prior cached prompt was only about 1,046 tokens including athlete details and core tools, so removing the athlete details risked putting the prefix below Sonnet 4.5's [1,024-token caching minimum](https://platform.claude.com/docs/en/build-with-claude/prompt-caching). The added text gives the static prefix room above that limit while reinforcing the current behavior. Tool selection remains keyword based; a different tool set can still require a separate cache entry because [tools precede system blocks in the cache key](https://platform.claude.com/docs/en/build-with-claude/prompt-caching).

Added `test_bot.py` to exercise a `save_fact` through the reply loop. It checks that the fact reaches the next call and persists, while the cached block remains identical across the tool round and the next message. It also checks that changing the athlete or date does not change that block. Updated `README.md` to describe the new boundary.

Verification: `python3 -m unittest -v` passes (2 tests). No live Claude request was made, so the actual cache token counts after this change have not been measured. The existing `logs/usage.jsonl` was left untouched.
