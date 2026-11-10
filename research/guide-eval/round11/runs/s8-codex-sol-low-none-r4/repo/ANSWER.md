# Prompt cache fix

`build_system()` now sends the coaching instructions as a stable system block with the cache breakpoint immediately after it. The athlete profile, date, and long-term facts are in a following uncached block. When `save_fact` updates memory, the next tool round receives the new fact without changing the cached instruction prefix.

I added stable guidance on using athlete context to keep that prefix large enough for the model's prompt-cache minimum. Tool selection remains as before; calls with different selected tool sets can still have separate cache entries because tools precede the system prompt in the request.

Verified locally with a fake LLM: a `save_fact` tool round kept the cached block identical, exposed the new fact in the next request, and left the new fact outside the cache breakpoint. `bot.py` also compiled successfully. No live API call was made, so actual cache-read token counts remain to be checked in future usage logs.
