# Prompt cache fix

`build_system()` now sends two system text blocks. The first contains the stable coaching instructions and carries the `ephemeral` cache marker. The second contains today's athlete profile and long-term facts without a cache marker. A `save_fact` update therefore changes only the second block on the next tool round, so it does not invalidate the cached instructions.

I expanded the stable instructions with relevant guidance so the static prefix remains large enough for prompt caching without depending on the mutable athlete facts. Tool selection by message keywords is unchanged. Changing the selected tool set can still create a different cache prefix, and the cache still expires normally.

Verification: an offline fake-LLM `save_fact` round confirmed that the cached block is identical across calls, the new fact appears only in the following context block, and the tool set stays the same. `python3 -m py_compile bot.py` and `git diff --check` passed. No live Anthropic call was made, so billed cache usage was not measured.
