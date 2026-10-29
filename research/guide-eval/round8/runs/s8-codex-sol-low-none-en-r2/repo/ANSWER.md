# Cache fix

The system prompt now has two text blocks. Stable coaching instructions end at the ephemeral cache breakpoint; the athlete profile and long-term facts come afterward. A `save_fact` update changes only that later block, so it no longer changes the cached instruction prefix. I added stable guidance to the instructions to keep the shorter prefix large enough for the model's cache minimum, and updated the README to describe the layout.

Verified with a local request-shape check: after adding a fact, the tools and cached block are identical, while the uncached athlete block includes the new fact. `python3 -m py_compile bot.py` and `git diff --check` passed. Live cache usage was not measured because no API call was made.
