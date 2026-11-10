# Prompt cache fix

`bot.py` now sends two cached system blocks. The first contains the coaching instructions and stable athlete profile; the second contains today's date and long-term facts. A `save_fact` changes only the second block, so the static prefix can be read from cache instead of being created again. The second cache marker still allows the full prompt to be reused when the context is unchanged.

I kept tool selection as it was. I added a short context-handling instruction to keep the stable cached prefix above the model's cache minimum, since the previous full prompt was only slightly above it.

Verified locally with assertions that a fact write and date change leave the first block identical while changing the second, and that both blocks retain cache markers. `python3 -m py_compile bot.py` and `git diff --check` passed. Actual cache token usage requires a live API call and was not measured.
