# Изменения в кешировании промпта

## Проблема
Ранее в `bot.py` функция `build_system` объединяла общие статические правила коучинга (`INSTRUCTIONS`) и динамический контекст атлета (`athlete_context`, куда входят дата, профиль и список фактов `facts`) в единый текстовый блок, на который вешался маркер `"cache_control": {"type": "ephemeral"}`:
```python
def build_system(a, today):
    # One block, cached as a whole: instructions + per-athlete context.
    text = INSTRUCTIONS + "\n\n" + athlete_context(a, today)
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]
```
Из-за этого при вызове инструмента `save_fact` в массив `facts` добавлялся новый факт, контекст атлета менялся, и префикс кеша инвалидировался целиком. В результате следующий запрос платил за полную повторную запись всего системного промпта в кеш (`cache_creation_input_tokens: ~1000`, `cache_read_input_tokens: 0`).

## Что сделано
В `bot.py` функция `build_system` разделена на два отдельных блока:
1. **Статический блок**: общие инструкции коучинга (`INSTRUCTIONS`), на котором установлен `cache_control: {"type": "ephemeral"}`. Размер инструкций превышает минимальный порог кеширования (1024 токена для Claude Sonnet). Этот блок теперь общий для всех пользователей и не зависит от добавления новых фактов или изменения даты.
2. **Динамический блок**: контекст конкретного атлета (`athlete_context(a, today)`), содержащий переменные данные (дату, цели, зоны и список долгосрочных фактов).

```python
def build_system(a, today):
    # Two blocks: static coaching instructions (cached across all athletes and turns)
    # and dynamic per-athlete context (facts, profile, date).
    return [
        {"type": "text", "text": INSTRUCTIONS, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": athlete_context(a, today)},
    ]
```

Теперь запись факта (`save_fact`) меняет только второй (динамический) блок, а статические инструкции продолжают читаться из префиксного кеша (`cache_read_input_tokens`), предотвращая пересоздание кеша для общих инструкций.
