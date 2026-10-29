# Причина ошибки и её исправление

## Причина (Why)

В логах (`logs/error.log`) зафиксирована ошибка при вызове `table.put_item(Item=item)`:
```text
TypeError: Float types are not supported. Use Decimal types instead.
```

1. При первой публикации таблица DynamoDB была пуста (`scan()` вернул пустой список `Items`). Функция `related()` вернула пустой список `similar: []`, и в сохраняемом объекте `item` не было дробных чисел (`float`). Публикация завершилась успешно (HTTP 201).
2. При второй публикации в таблице уже существовала одна статья. Функция `related()` вычислила сходство между новой статьёй и уже существующей с помощью функции `similarity(story, other)`. Функция `similarity` возвращала значение типа `float` (`round(...)`).
3. Библиотека `boto3` (и её сериализатор DynamoDB `TypeSerializer`) не поддерживает тип Python `float` для числовых атрибутов DynamoDB и требует использования `decimal.Decimal` во избежание потери точности с плавающей точкой.
4. Попытка записать объект со значением `score` типа `float` привела к `TypeError`, который был перехвачен общим блоком `except Exception` в `handler()` и вернул HTTP 500.

## Исправление (Fix)

В файле [`src/app.py`](src/app.py):
1. Импортирован класс `Decimal` из стандартного модуля `decimal`:
   ```python
   from decimal import Decimal
   ```
2. Значение сходства в функции `similarity()` преобразуется в `Decimal`:
   ```python
   return Decimal(str(round(0.7 * tag_score + 0.3 * word_score, 4)))
   ```
3. В тесты [`tests/test_publish.py`](tests/test_publish.py) добавлен тест `test_publish_second_story_with_similarity`, проверяющий успешную вторую публикацию при наличии ранее созданных статей и корректность типа `Decimal` для поля `score` в списке `similar`.
