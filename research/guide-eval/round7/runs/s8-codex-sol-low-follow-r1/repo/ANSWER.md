# Prompt cache fix

Changed `build_system()` in `bot.py` to send two text blocks, each marked `cache_control: {"type": "ephemeral"}`. The first contains only the byte-stable coaching instructions. The second contains the date and athlete context, including long-term facts. A `save_fact` update therefore changes the second cache segment while leaving the instruction segment reusable.

The existing tool selection and usage logging are unchanged. I verified locally that adding a fact leaves the first block identical, changes the second block, and retains both cache markers. `python3 -m py_compile bot.py` also passed. No live Claude request was made, so the expected cache read and creation token counts have not been measured here.
