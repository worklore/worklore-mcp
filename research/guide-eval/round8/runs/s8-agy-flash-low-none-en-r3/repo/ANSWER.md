# Changes to Prompt Caching

## Cause of the Issue
Previously, `build_system()` concatenated the static coaching rules (`INSTRUCTIONS`) and the dynamic athlete information (`athlete_context(a, today)`) into a single text block with `cache_control: {"type": "ephemeral"}`:

```python
def build_system(a, today):
    text = INSTRUCTIONS + "\n\n" + athlete_context(a, today)
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]
```

Because Anthropic prompt caching evaluates prefixes byte-for-byte, any change to `a.facts` via `save_fact` modified the content of this single system block. This invalidated the entire cached block, causing the subsequent API call to suffer a cache miss and pay full price (`cache_read_input_tokens: 0`, recreating the cache) for the static instructions and tools.

## Fix
In `bot.py`, `build_system()` was updated to separate the system prompt into two distinct content blocks:
1. The static instructions (`INSTRUCTIONS`) with `cache_control: {"type": "ephemeral"}`.
2. The dynamic athlete context (`athlete_context(a, today)`) without cache control.

```python
def build_system(a, today):
    return [
        {"type": "text", "text": INSTRUCTIONS, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": athlete_context(a, today)},
    ]
```

Since Anthropic processes prompt prefix caching in sequence (`tools` -> `system` -> `messages`), placing the cache breakpoint on the static `INSTRUCTIONS` content block allows the static instructions (and preceding tool definitions) to remain cached even when new facts are appended to the athlete record.
