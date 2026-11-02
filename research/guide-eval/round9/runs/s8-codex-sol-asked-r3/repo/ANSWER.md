# Prompt cache fix

`build_system()` now sends the fixed coaching instructions and the athlete context as two separate text blocks, each with an `ephemeral` cache marker. A `save_fact` changes the second block while the instruction block stays byte-identical, so the static prefix can be reused instead of being rebuilt with the facts.

Tool selection and usage logging are unchanged. I verified locally that adding a fact leaves the first block identical, changes the second block, and preserves both cache markers. `python3 -m py_compile bot.py` and `git diff --check` pass. I did not make live API calls, so the resulting `cache_read_input_tokens` and `cache_creation_input_tokens` have not been measured.
