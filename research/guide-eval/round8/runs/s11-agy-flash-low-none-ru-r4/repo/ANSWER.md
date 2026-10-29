# Причина ошибки 500 и решение

## Причина

При первой публикации (`POST /stories`) таблица DynamoDB пуста (`existing = []`). Список похожих историй `similar` оказывается пустым (`[]`), и в элемент DynamoDB не попадают числа с плавающей точкой (`float`). Запрос завершается успешно со статусом 201.

При второй (и последующих) публикации в таблице уже есть существующие записи. Функция `publish()` вызывает `related(story, existing)`, где для каждой существующей статьи рассчитывается показатель сходства `similarity()`, возвращавший значение типа `float` (`round(...)`). Полученные объекты вида `{"slug": other["slug"], "score": similarity(...)}` попадают в список `similar` атрибутов элемента.

Библиотека `boto3` (и её сериализатор типов DynamoDB `TypeSerializer`) не поддерживает тип `float` при сохранении данных в DynamoDB, требуя использовать тип `Decimal` (`TypeError: Float types are not supported. Use Decimal types instead.`). Из-за этого вызов `table.put_item(Item=item)` завершался исключением `TypeError`, которое перехватывалось в `handler` и возвращало HTTP 500:
```
TypeError: Float types are not supported. Use Decimal types instead.
```

## Исправление

1. В модуле `src/app.py`:
   - Импортирован класс `Decimal` из модуля `decimal`.
   - В функции `similarity()` результат вычисления преобразован в `Decimal(str(round(...)))`.

2. В тестах `tests/test_publish.py`:
   - Добавлен юнит-тест `test_publish_second_story_calculates_similarity_without_error`, проверяющий успешную публикацию второй статьи при наличии первой, а также корректность типа `Decimal` для поля `score` в списке `similar`.
