# Prompt cache fix

`build_system()` now sends the coaching instructions and athlete context as separate system text blocks, each with an ephemeral cache breakpoint. A `save_fact` changes only the second block, so the unchanged instruction prefix can be read from cache while the updated context is cached separately. The context breakpoint also keeps subsequent tool-loop rounds and messages eligible to reuse the full prompt.

I added stable guidance consistent with the existing coaching rules so the instruction prefix remains large enough for prompt caching's minimum prefix size, even without athlete facts. Tool selection and memory persistence are unchanged.

Verified locally that adding a fact changes only the context block, both breakpoints remain present, and `bot.py` compiles. No live API call was made.
