# Причина ошибки и исправление

## Причина сбоя (500) при второй публикации

1. **Первая публикация**:
   - При первой публикации таблица DynamoDB пустая (`existing = []`).
   - Функция `related(story, existing)` возвращает пустой список `[]` для поля `similar`.
   - В сохраняемом объекте `similar: []` нет никаких числовых значений с плавающей точкой (`float`), поэтому вызов `table.put_item(Item=item)` проходит успешно (код 201).

2. **Вторая публикация**:
   - В таблице уже есть одна статья (`existing` содержит 1 элемент).
   - Функция `related(story, existing)` вычисляет сходство с помощью `similarity(story, other)`.
   - Функция `similarity` возвращала число типа `float` (`round(..., 4)`).
   - Поле `similar` формировалось как `[{"slug": "...", "score": 0.xxxx}]`.
   - Библиотека `boto3` (в частности, сериализатор типов DynamoDB `TypeSerializer`) намеренно **не поддерживает** тип Python `float` из-за возможной потери точности и требует использования `decimal.Decimal` (ошибка: `TypeError: Float types are not supported. Use Decimal types instead.`).
   - Исключение `TypeError` перехватывалось общим блоком `except Exception:` в `handler()`, логировалось в `error.log` и приводило к ответу со статусом `500`.

## Внесенные исправления

1. В [`src/app.py`](src/app.py):
   - Добавлен импорт класса `Decimal`:
     ```python
     from decimal import Decimal
     ```
   - В функции `similarity` результат вычисления возвращается как `Decimal` вместо `float`:
     ```python
     return Decimal(str(round(0.7 * tag_score + 0.3 * word_score, 4)))
     ```
   Теперь при наличии уже опубликованных статей значение поля `score` в списке `similar` сериализуется как DynamoDB Number (`Decimal`), что предотвращает возникновение `TypeError`.

2. В [`tests/test_publish.py`](tests/test_publish.py):
   - Добавлен тест `test_publish_second_story_with_similarity`, проверяющий последовательную публикацию двух статей и расчет `similar`, чтобы регрессия была исключена.
