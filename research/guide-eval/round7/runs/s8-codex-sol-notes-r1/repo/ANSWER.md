# Prompt cache fix

`build_system()` now sends two text blocks with `cache_control: ephemeral`: the shared coaching instructions first, followed by the date and athlete context. A `save_fact` write changes only the second block, so the unchanged instruction prefix can still be read from cache. Tool selection and the tool-use loop are unchanged.

Verified locally that a `save_fact` call changes the athlete context block while leaving the instruction block and selected tools identical. No live API call was made, so cache token counts were not measured after the change.
