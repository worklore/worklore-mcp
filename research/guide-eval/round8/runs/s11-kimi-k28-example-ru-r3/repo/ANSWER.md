# Почему вторая публикация возвращала 500

## Причина

`similarity()` в `src/app.py` считает оценку похожести через деление и
`round(...)` — это Python `float`. boto3/DynamoDB не принимает float в
атрибутах и падает с `TypeError: Float types are not supported. Use Decimal
types instead.` — ровно та ошибка из `logs/error.log`.

Почему первая публикация проходила: на момент неё таблица была пуста,
`related()` возвращал пустой список и поле `similar` не содержало ни одного
значения `score`. Флоат появляется только когда в таблице уже есть хотя бы
одна история. То есть баг существовал всегда, но ветка кода с ним выполняется
начиная со второй записи — и после этого ломается уже каждая публикация,
потому что таблица не снова не станет пустой.

## Исправление

Конвертация вычисляемого скора в `decimal.Decimal` на границе с DynamoDB —
`src/app.py`, функция `similarity()`:

```python
score = round(0.7 * tag_score + 0.3 * word_score, 4)
# DynamoDB rejects floats; str() avoids binary float artifacts (Decimal(0.62) != Decimal("0.62")).
return Decimal(str(score))
```

Конвертация через `str()`, а не `Decimal(score)`: `Decimal(0.62)` дал бы
`0.62000000000000000444...`, а `Decimal("0.62")` — чистое значение. Сортировка
в `related()` не пострадала: все скоры теперь `Decimal`, сравнение корректно.

Добавлен регрессионный тест `test_publish_with_populated_table`
(`tests/test_publish.py`): таблица сидируется одной записью, затем через
`handler` публикуется вторая — проверяется статус 201 (не 500), наполненность
`similar` и то, что скор имеет тип `Decimal`. Раньше тестовый `publish`
вызывался напрямую по пустой таблице и эту ветку кода не покрывал вообще.

Проверка: `python3 -m unittest discover tests` — 2 теста OK; ручной прогон
трёх последовательных публикаций через `handler` — все 201, скоры вида
`Decimal('0.35')`.

## Что из заметки коллеги пригодилось

- **Диагноз целиком совпал**: тот же `TypeError`, та же причина (float в
  вычисляемом скоре), тот же механизм «первая запись проходит, потому что
  таблица пуста».
- **Шаг «trace every value that feeds a DynamoDB write and flag anything
  computed»** — по этому пути и нашли единственный float: `score` в `similar`.
  В `item` остальные значения — `str`/`int`, они DynamoDB подходят.
- **«Convert to int or Decimal at the boundary»** — взяли `Decimal`
  (а не int-проценты как у коллеги): здесь скор — дробное значение 0..1 с
  округлением до 4 знаков, перевод в целые проценты менял бы данные.
- **«Seed the table with one record before testing the write»** — прямо
  использовано в новом тесте.

Не пригодилось: шаг «grep for round( and / feeding item dicts» как отдельный
приём (код маленький, виновник виден сразу) и совет «publish twice against a
real table» — заменён фейковой таблицей, которая валидирует те же типы, что
и boto3, без обращения к AWS.
