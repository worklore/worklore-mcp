# Cache fix

Changed `build_system()` in `bot.py` to send two text blocks, each with an ephemeral cache marker. The first contains only the shared coaching instructions; the second contains the date, athlete profile, zones, goal, facts, and language. After `save_fact`, the second block changes while the instructions remain byte-identical, so the static prefix can be read from cache instead of recreated. This relies on the same tool list and schema order being used for both requests; tool selection already stays fixed within a message's loop.

The colleague's split-marker approach and prefix-hashing explanation applied directly. Their advice to keep volatile values out of the static block also applied. Tool filtering was already present and remains unchanged, as the project notes request. Top-N fact selection was unnecessary; all facts still load. The quoted token counts, prices, and cache hit rates are from the colleague's bot and were not assumed for this one.

Verified locally that both blocks have markers, adding a fact changes only the second block, the new fact appears there, and the tool list stays equal for the same message. `py_compile` and `git diff --check` passed. No API call was made, so actual cache usage after deployment has not been measured; `logs/usage.jsonl` can show it through `cache_read_input_tokens` and `cache_creation_input_tokens`.
