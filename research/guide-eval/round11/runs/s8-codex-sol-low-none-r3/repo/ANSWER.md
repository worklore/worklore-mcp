# Cache fix

Split the system prompt in `bot.py` into two cached text blocks: stable coaching instructions first, then the athlete context. A `save_fact` update now changes only the second block, allowing the first cached prefix to be reused. Added stable guidance to keep that first prefix above the model's minimum cacheable length. Tool selection and the fresh athlete context on each call remain intact.

Verified locally that adding a fact leaves the first block and selected tools unchanged while updating the second block. `python3 -m py_compile bot.py` passes. Live cache usage was not tested because that would require an API call.
