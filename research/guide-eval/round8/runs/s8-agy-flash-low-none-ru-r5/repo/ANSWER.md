# Изменения в кешировании промпта

## Проблема
Ранее в `bot.py` функция `build_system(a, today)` объединяла статические инструкции коучинга (`INSTRUCTIONS`) и динамический профиль атлета (`athlete_context(a, today)`) в один текстовый блок с маркером кеширования:

```python
def build_system(a, today):
    text = INSTRUCTIONS + "\n\n" + athlete_context(a, today)
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]
```

При вызове инструмента `save_fact`:
1. В список фактов атлета `a.facts` добавлялся новый факт.
2. В цикле обработки сообщений (`round 2`) или в следующем сообщении заново вызывался `build_system(a, today)`.
3. Поскольку текст всего блока менялся из-за добавления факта в `athlete_context`, Anthropic API не находил точного совпадения префикса кеша (`cache_read_input_tokens: 0`) и заново создавал кеш полного промпта (`cache_creation_input_tokens > 1000`), приводя к двойной оплате токенов при каждом сохранении факта.

## Что изменено
В [bot.py](bot.py) системный промпт в `build_system` разделен на два отдельных блока:
1. **Статический блок**: общие инструкции коучинга (`INSTRUCTIONS`) с маркером `cache_control: {"type": "ephemeral"}`. Этот блок не зависит от профиля атлета и его фактов, поэтому стабильно считывается из кеша между раундами вызова инструментов и между сообщениями (а также повторно используется для всех атлетов).
2. **Динамический блок**: контекст конкретного атлета (`athlete_context(a, today)`) без маркера кеширования. Он идет после закешированных статических инструкций и передается как обычный динамический контекст.

Код функции `build_system` обновлен следующим образом:

```python
def build_system(a, today):
    # Static coaching rules are cached; per-athlete dynamic context is separate
    # so updates (e.g. save_fact) do not invalidate the cached instructions.
    return [
        {"type": "text", "text": INSTRUCTIONS, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": athlete_context(a, today)},
    ]
```

В результате при вызове `save_fact` префикс со статическими инструкциями остается неизменным и считывается из кеша, предотвращая сброс кеша инструкций.
