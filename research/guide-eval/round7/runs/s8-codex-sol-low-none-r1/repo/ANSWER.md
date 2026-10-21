# Prompt cache fix

Split the system prompt into two blocks. The cache breakpoint now ends after the coaching instructions and stable athlete profile (name, sport, zones, goal, language). The current date and long-term facts follow in an uncached block, so `save_fact` changes only text after the breakpoint. Added stable coaching guidance to keep the reusable prefix above Claude's minimum cache size.

Verified locally that adding a fact and changing the date leave the cached block identical while updating the following block. `python3 -m py_compile bot.py` and `git diff --check` pass. Live cache usage was not tested because it requires an API call.
