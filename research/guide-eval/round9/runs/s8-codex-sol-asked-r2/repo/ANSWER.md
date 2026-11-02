# Prompt cache fix

`build_system()` now sends two text blocks with `cache_control: ephemeral`: the byte-stable coaching instructions first, then the athlete-specific context (date, profile, zones, goal, facts, and language). When `save_fact` changes the context, the static instructions retain their cache prefix and only the context tail needs a new cache entry. The existing tool selection and usage logging are unchanged.

Added `test_prompt_cache.py` to check that a fact write changes only the second block and that different athletes and dates share the same static block.

Verification: `python3 -m unittest -v test_prompt_cache.py` passed (2 tests); `git diff --check` passed. No live Anthropic call was made, so cache token counts after the change remain unmeasured. The existing `logs/usage.jsonl` documents the prior full-prompt misses after `save_fact`.
