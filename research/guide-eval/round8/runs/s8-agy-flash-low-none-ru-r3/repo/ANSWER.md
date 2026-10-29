# Изменения в кешировании промпта

## Проблема
Ранее в `bot.py` функция `build_system` склеивала статические правила тренера (`INSTRUCTIONS`) и динамический контекст атлета (`athlete_context(a, today)`, включающий список фактов `facts`) в один блок текста:

```python
text = INSTRUCTIONS + "\n\n" + athlete_context(a, today)
return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]
```

Из-за этого при добавлении нового факта через `save_fact`:
1. Менялся текст всего системного блока.
2. Инвалидировался кеш всего блока целиком, включая неизменяемую инструкцию (~1000 токенов).
3. В следующем запросе `cache_read_input_tokens` падал до 0, а за весь системный промпт повторно списывалась полная стоимость создания кеша (`cache_creation_input_tokens`).

## Решение
В Anthropic Messages API системный промпт может передаваться как список контентных блоков с отдельными маркерами `cache_control` на каждом контрольном пункте (до 4 блоков с кешированием).

В функции `build_system` системный промпт разделен на два отдельных текстовых блока:
1. **Статический блок**: `INSTRUCTIONS` с маркером `cache_control: {"type": "ephemeral"}`. Он неизменен между вызовами и между всеми пользователями/атлетами, поэтому его кеш сохраняется и успешно переиспользуется (`cache_read_input_tokens`), даже если у атлета обновляются факты или меняется контекст.
2. **Динамический блок**: `athlete_context(a, today)` с маркером `cache_control: {"type": "ephemeral"}`. Кеширует профиль, зоны и факты конкретного атлета на время сессии (между раундами tool use и повторными сообщениями).

```python
def build_system(a, today):
    return [
        {"type": "text", "text": INSTRUCTIONS, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": athlete_context(a, today), "cache_control": {"type": "ephemeral"}},
    ]
```
