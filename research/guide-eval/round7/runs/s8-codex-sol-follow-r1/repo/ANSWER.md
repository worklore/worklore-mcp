# Prompt cache fix

`build_system()` now sends two text blocks, each with `cache_control: {"type": "ephemeral"}`. The first contains only the fixed `INSTRUCTIONS`; the second contains the date, athlete profile, zones, goal, facts, and language. A `save_fact` update changes the second block while leaving the first block byte-identical, so Claude can reuse the static prefix and create a new cache entry for the athlete context.

The existing per-message tool selection and its order are unchanged. The selected tool list remains fixed across rounds of one tool-use loop.

Added `test_bot.py` to check both cache boundaries, the static block across athletes, and the changed fact tail. `python3 -m unittest -v test_bot.py`, `python3 -m py_compile bot.py`, and `git diff --check` pass.

Live cache token counts were not verified because that requires an Anthropic API call. In `logs/usage.jsonl`, after a `save_fact`, the expected result is a nonzero `cache_read_input_tokens` value for the static prefix and `cache_creation_input_tokens` for the changed tail, rather than a full-prompt cache creation.
