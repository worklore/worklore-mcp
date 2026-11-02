# Prompt cache fix

`build_system()` now sends two Anthropic text blocks with separate `cache_control: ephemeral` markers. The first contains only the fixed coaching instructions; the second contains the date and athlete context, including long-term facts. After `save_fact` changes that context, the fixed instruction block remains byte-identical, so the changed tail no longer invalidates its cache breakpoint.

I verified locally that adding a fact changes only the second system block while the first block and selected tools stay identical. No API call was made, so cache read and creation token counts after this change still need a live check in `logs/usage.jsonl`.
