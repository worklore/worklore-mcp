# Изменения в кешировании системного промпта

## Проблема
Ранее в `bot.py` функция `build_system(a, today)` объединяла статические правила коучинга (`INSTRUCTIONS`) и динамический профиль атлета (`athlete_context(a, today)`) в один текстовый блок с маркером кеширования `{"type": "ephemeral"}`:

```python
def build_system(a, today):
    # One block, cached as a whole: instructions + per-athlete context.
    text = INSTRUCTIONS + "\n\n" + athlete_context(a, today)
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]
```

Так как при вызове `save_fact` в список фактов атлета (`a.facts`) добавлялась новая запись, строка `athlete_context(a, today)` менялась. В результате весь объединённый блок менялся по префиксу, кеш инвалидировался, и следующий запрос заново оплачивал создание кеша (`cache_creation_input_tokens`) для всех статических инструкций (~1000 токенов).

## Решение
Разделили системный промпт на два отдельных блока контента:
1. **Статический блок**: общие правила тренера (`INSTRUCTIONS`) с маркером `cache_control: {"type": "ephemeral"}`. Этот блок неизменен между запросами и пользователями, поэтому стабильно читается из кеша (`cache_read_input_tokens`).
2. **Динамический блок**: контекст конкретного атлета (`athlete_context(a, today)`), включающий дату, цели, зоны и список долгосрочных фактов (`facts`).

Реализация в [`build_system`](file:///tmp/h-oaAuFb/bot.py#L130-L136):
```python
def build_system(a, today):
    # Two blocks: static coaching rules cached separately from dynamic athlete context
    # so that memory updates (save_fact) or date changes do not bust the instructions cache.
    return [
        {"type": "text", "text": INSTRUCTIONS, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": athlete_context(a, today)},
    ]
```

Теперь сохранение новых фактов в память (`save_fact`) или смена даты затрагивает только динамическую часть и больше не инвалидирует кеш статических инструкций.
