# Prompt cache fix

`build_system()` now sends two text blocks, each with `cache_control: {"type": "ephemeral"}`. The first contains only the constant coaching instructions. The second contains the date, athlete profile, zones, goal, facts, and language. A `save_fact` update changes the second block while leaving the first block byte-identical, so it can reuse the static prefix cache.

The colleague's two-cache-boundary approach applies here. Its advice to keep tool schemas and their order stable also applies; the existing keyword-based tool filtering remains in place, with a fixed selection throughout each tool loop. Its advice against per-message fact selection applies too: the bot already includes all facts, so no selection was added. The note's token savings and five-minute live verification figures are examples from another bot, not measurements of this change.

Local verification built the prompt before and after adding a fact: the static block stayed equal, the athlete block changed, both blocks had cache markers, and the core tool selection stayed the same. No API calls were made, so actual `cache_read_input_tokens` and `cache_creation_input_tokens` after this change have not been measured. `logs/usage.jsonl` already records both fields for later verification.
