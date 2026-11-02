# Prompt Caching Optimization

## Problem
Previously, `build_system()` combined the static `INSTRUCTIONS` text and the volatile `athlete_context()` into a single text block with one `cache_control: {"type": "ephemeral"}` marker. Because Anthropic's prompt caching relies on a prefix hash, whenever a new fact was recorded via `save_fact`, the volatile tail changed, invalidating the entire cached block. Consequently, the next API call had to pay full price (`cache_creation_input_tokens`) to re-cache the entire system prompt (~1,000+ tokens, including all static coaching rules).

## Changes Made
In [bot.py](file:///private/tmp/h-Mn0qJ6/bot.py), updated `build_system(a, today)` to return a two-segment system prompt, placing a `cache_control: {"type": "ephemeral"}` marker on each segment:

1. **Static Instruction Block**: Contains the immutable `INSTRUCTIONS` text (~780 tokens), which remains byte-identical across athletes, sessions, and memory updates.
2. **Volatile Context Block**: Contains the athlete-specific profile, date, zones, goal, language, and dynamic facts (`athlete_context(a, today)`).

```python
def build_system(a, today):
    # Two blocks with cache_control: ephemeral:
    # 1. Static instructions (byte-identical across athletes and calls)
    # 2. Athlete context (volatile: date, profile, long-term facts, language)
    # This prevents memory writes (save_fact) from evicting the static instruction cache.
    return [
        {"type": "text", "text": INSTRUCTIONS, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": athlete_context(a, today), "cache_control": {"type": "ephemeral"}},
    ]
```

## Result
When `save_fact` appends a new fact to `data/athletes.json`, only the second (volatile context) block is invalidated. The first block holding the static coaching instructions stays cached as a hot prefix, ensuring subsequent calls read the static instructions from cache rather than paying for the whole system prompt.
