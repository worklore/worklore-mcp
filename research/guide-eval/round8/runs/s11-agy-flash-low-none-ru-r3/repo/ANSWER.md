# Причина ошибки 500 и её исправление

## 1. Причина ошибки

При первой публикации таблица DynamoDB пуста (`existing = []`). Список похожих историй `similar` получается пустым (`[]`), и в элемент DynamoDB сохраняется пустой список. Ошибки не возникает, запрос завершается со статусом 201 (`similar=0 stored`).

При второй (и последующих) публикациях в таблице уже есть существующие истории (`existing` не пустой). Функция `related()` вызывает функцию `similarity(a, b)`, которая возвращает вещественное число типа `float` (`round(..., 4)`):

```python
scored.append({"slug": other["slug"], "score": similarity(story, other)})
```

При попытке вызова `table.put_item(Item=item)` сериализатор типов DynamoDB (`boto3.dynamodb.types.TypeSerializer`) обходит структуру данных и проверяет типы полей. В `boto3` тип `float` не поддерживается для атрибутов чисел DynamoDB из-за потенциальных проблем с точностью представления чисел с плавающей точкой в стандарте IEEE-754. Выбрасывается исключение:

```
TypeError: Float types are not supported. Use Decimal types instead.
```

В блоке `handler` исключение перехватывается общим обработчиком `except Exception:`, логируется и клиенту возвращается статус 500.

## 2. Исправление

В файле `src/app.py`:
1. Импортирован класс `Decimal` из стандартного модуля `decimal`.
2. Функция `similarity(a, b)` возвращает объект `Decimal(str(round(0.7 * tag_score + 0.3 * word_score, 4)))` вместо значения типа `float`.
3. В `tests/test_publish.py` добавлен тест `test_publish_second_story_calculates_similarity_without_dynamo_type_error`, проверяющий успешную публикацию второй истории при непустой таблице.
