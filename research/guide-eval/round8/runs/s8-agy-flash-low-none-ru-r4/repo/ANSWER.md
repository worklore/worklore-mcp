# Изменения в кешировании промпта

## Проблема
Ранее в `build_system()` статические инструкции коучинга (`INSTRUCTIONS`) и динамический контекст атлета (`athlete_context(a, today)`: дата, профиль, зоны, факты из долговременной памяти) склеивались в один текстовый блок с маркером `"cache_control": {"type": "ephemeral"}`:

```python
def build_system(a, today):
    text = INSTRUCTIONS + "\n\n" + athlete_context(a, today)
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]
```

Из-за этого любое добавление нового факта через `save_fact` (или смена дня / изменение профиля) приводило к инвалидации всего кеша, включая неизменяемую инструкцию (~1000 токенов). Следующий вызов API сбрасывал кеш (`cache_read_input_tokens: 0`) и заново создавал кеш полного системного промпта (`cache_creation_input_tokens` ~1000).

## Решение
В [bot.py](file:///tmp/h-rLPv0s/bot.py) системный промпт разделен на два отдельных блока контента:
1. **Статический блок** (`INSTRUCTIONS`) с маркером кеширования `cache_control: {"type": "ephemeral"}`.
2. **Динамический блок** (`athlete_context(a, today)`), содержащий профиль атлета, дату и факты памяти, который идет после статического блока без маркера кеширования.

```python
def build_system(a, today):
    # Static coaching instructions (shared across athletes) are cached first.
    # Dynamic per-athlete context (facts, profile, date) follows in a separate block.
    return [
        {"type": "text", "text": INSTRUCTIONS, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": athlete_context(a, today)},
    ]
```

## Результат
- Статические инструкции сохраняются в префиксном кеше Claude Prompt Caching и повторно читаются из кеша даже при обновлении фактов атлета.
- Запись нового факта через `save_fact` модифицирует только незакешированный суффикс (контекст атлета) и больше не инвалидирует кеш статических инструкций.
- Кеш инструкций теперь также переиспользуется между разными атлетами.
