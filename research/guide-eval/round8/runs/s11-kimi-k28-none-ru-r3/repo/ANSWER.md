# Почему вторая публикация возвращала 500

## Причина

`similarity()` в `src/app.py` возвращала `float` (`round(0.7 * tag_score + 0.3 * word_score, 4)`),
и этот float попадал в поле `similar[].score` сохраняемого item. DynamoDB не поддерживает
float — boto3 бросает `TypeError: Float types are not supported. Use Decimal types instead.`

Первая публикация проходила, потому что таблица была пуста: `existing` пустой →
`similar` = `[]` → ни одного float в item → `put_item` успешен (это и есть строка
`similar=0 stored` в логе). Со второй публикации в таблице уже есть истории,
`related()` кладёт в item словарь с float-полем `score`, и каждый `put_item`
падает с этой TypeError, оборачиваясь в 500 (`logs/error.log`, строки 27–35).

## Исправление (src/app.py)

1. Корень дефекта: `similarity()` теперь считает в `Decimal` и возвращает `Decimal`
   (арифметика `Decimal(len(...) / len(...))`, веса `Decimal("0.7")` / `Decimal("0.3")`).
2. Страховка от повторения класса ошибки: `publish()` перед `put_item` прогоняет item
   через `dynamo_safe()` — рекурсивно конвертирует любые float в Decimal. Если в будущем
   в item добавится ещё одно float-поле, оно не уронит endpoint.

## Тест

`tests/test_publish.py`: `test_second_publish_stores_similar_as_decimal` публикует две
истории и проверяет, что score в `similar` — `Decimal`, а таблица приняла оба item.
Прогон: `python3 -m unittest discover tests` — 2 теста OK.
