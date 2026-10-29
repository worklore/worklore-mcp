# Cache fix

`build_system` now sends the coaching instructions as a cached system block and the athlete context as a separate, unmarked block. A `save_fact` changes only the athlete block, so the next request can reuse the static instruction prefix when the selected tools and cache window match. I added stable coaching examples to give that prefix enough content for the model's cache threshold, and updated the README to describe the new layout.

Verified locally that a new fact changes the athlete block while the cached block and selected tools stay identical. `python3 -m py_compile bot.py` and `git diff --check` passed. No live API call was made, so cache-read token counts were not measured.
