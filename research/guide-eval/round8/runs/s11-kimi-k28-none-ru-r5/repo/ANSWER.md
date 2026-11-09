# Почему вторая публикация возвращала 500

## Причина

`similarity()` (`src/app.py`) возвращала `float` — `round(0.7 * tag_score + 0.3 * word_score, 4)`.
Этот счёт попадает в атрибут `similar` элемента DynamoDB, а boto3/DynamoDB не поддерживают
`float`: `put_item` падает с `TypeError: Float types are not supported. Use Decimal types instead.`,
и `handler` превращает исключение в 500.

Первая публикация после деплоя проходила случайно: таблица была пуста, `related()` вернул
пустой список `similar`, и в элемент не попадало ни одного float. Со второй публикации
в таблице уже была хотя бы одна история, в `similar` попадали `{slug, score: float}` —
и каждая следующая публикация падала с 500. Лог это подтверждает: `similar=0 stored`
и `201` при первом запросе, затем `TypeError` в `put_item` и `500` при каждом следующем.

Воспроизведение (до исправления): `publish()` в пустую таблицу — 201;
второй `publish()` — `TypeError: Float types are not supported`.

## Исправление

- `src/app.py` — `similarity()` теперь возвращает `Decimal(str(round(..., 4)))`:
  тот же округлённый счёт, но в типе, который DynamoDB принимает. Конверсия через `str`
  нужна, чтобы избежать бинарных артефактов float (`Decimal(0.35)` дал бы
  `0.34999999999999997779...`).
- `tests/test_publish.py` — регрессионный тест `test_publish_with_existing_story_stores_decimal_scores`:
  публикует две истории (сценарий из лога) и проверяет, что вторая сохраняется
  и её `score` имеет тип `Decimal`.

## Проверка

- `python3 -m unittest discover tests` — оба теста проходят.
- Сквозная проверка через `handler()`: два подряд `POST /stories` → `201`, `201`,
  в таблице `score: Decimal('0.5333')`.
