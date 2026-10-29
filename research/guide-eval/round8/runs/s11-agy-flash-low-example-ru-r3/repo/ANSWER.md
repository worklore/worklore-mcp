# Причина ошибки 500 и решение

## 1. Причина сбоя при второй публикации

При первой публикации (`POST /stories`) таблица `stories` в DynamoDB пуста. Функция `table.scan()` возвращает пустой список существующих записей (`existing = []`). Список похожих историй `similar = related(story, existing)` оказывается пустым (`[]`). Соответственно, в сохраняемом объекте `item` нет вычисленных оценок схожести, и `table.put_item(Item=item)` выполняется успешно.

При второй публикации в таблице уже есть как минимум одна запись. Функция `related(story, existing)` вызывает `similarity(story, other)`, где выполняется вычисление:
```python
round(0.7 * tag_score + 0.3 * word_score, 4)
```
Результатом является число с плавающей точкой Python (`float`). Поле `similar` заполняется списком словарей вида `[{"slug": ..., "score": 0.35}]`.

В `boto3` сериализатор типов DynamoDB (`TypeSerializer` / `_get_dynamodb_type`) не поддерживает стандартный тип Python `float` из-за особенностей внутреннего формата DynamoDB Number (который требует точного десятичного строкового представления). Попытка сериализовать `float` вызывает исключение:
```
TypeError: Float types are not supported. Use Decimal types instead.
```
В функции `handler()` неперехваченное исключение логируется (`log.exception("publish failed")`), и возвращается ответ `500 Internal Server Error`.

---

## 2. Внесённые исправления

1. **Использование `Decimal` для `score`**:
   В [src/app.py](file:///tmp/h-ixQYyM/src/app.py) функция `similarity(a, b)` теперь преобразует результат вычисления в `Decimal`:
   ```python
   from decimal import Decimal

   def similarity(a, b):
       ta, tb = set(a.get("tags", [])), set(b.get("tags", []))
       tag_score = len(ta & tb) / len(ta | tb) if (ta | tb) else 0
       wa, wb = words(a.get("body")), words(b.get("body"))
       word_score = len(wa & wb) / len(wa | wb) if (wa | wb) else 0
       return Decimal(str(round(0.7 * tag_score + 0.3 * word_score, 4)))
   ```
   Преобразование через `str(...)` гарантирует отсутствие артефактов двоичного представления `float`. Теперь DynamoDB успешно принимает значение как тип Number.

2. **Добавление тестов на непустую базу данных**:
   В [tests/test_publish.py](file:///tmp/h-ixQYyM/tests/test_publish.py) добавлены тесты:
   - `test_publish_second_story_succeeds_with_similarity_scores` — проверяет сохранение второй истории при наличии первой, валидируя вычисление схожести и запись в FakeTable без ошибок типизации.
   - `test_handler_second_publish_success` — проверяет сквозную работу обработчика `handler()` при двух последовательных запросах (оба возвращают HTTP 201).

---

## 3. Какие части заметки коллеги пригодились

### Что пригодилось:
- **Диагноз проблемы**: Указание на то, что `boto3` / DynamoDB не принимает `float` и требует `Decimal` либо `int`.
- **Объяснение, почему первая публикация прошла успешно**: На пустой таблице ветка кода с вычислением схожести и записью `score` не порождала значений, так как список `similar` был пуст.
- **Подход к тестированию (Seeded state test)**: Рекомендация обязательно писать тесты, которые тестируют запись при уже заполненной таблице (write against populated/seeded state), так как состояние базы данных активирует зависимую логику (similarity, deduplication, scoring).

### Что было пропущено / адаптировано:
- Автор заметки перешёл на целочисленные проценты (`int`), однако в нашем сервисе удобнее и точнее сохранить 4 знака после запятой с помощью `Decimal(str(...))`, что полностью поддерживается спецификацией DynamoDB и `boto3`.
