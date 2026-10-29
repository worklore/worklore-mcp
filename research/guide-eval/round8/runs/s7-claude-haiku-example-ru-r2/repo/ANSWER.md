# Intervals.icu: почему атлеты не могут подключиться

Атлеты не могли подключиться по четырём независимым причинам. Три из них подтверждены логами и воспроизведены локально, четвёртая объясняет «expired, reconnect» через час.

## Причины

1. **Кнопка Connect — GET-ссылка, а SPA шлёт токен только в заголовке fetch.**
   `static/app.js` рендерил `<a href="/api/intervals/auth/init">`. Переход по ссылке — это навигация страницы, и `Authorization: Bearer` в ней не уходит. Сервер отвечает 401 `{"error":"unauthorized"}`. Это ровно то, что видно в `logs/connect-attempt.log`, раздел 1, и в тикете #214.

2. **Authorize-шаг отклоняется: в scope одни области указаны дважды.**
   `config.SCOPES` содержал `ACTIVITY:READ,ACTIVITY:WRITE` и `CALENDAR:READ,CALENDAR:WRITE`. `:WRITE` уже включает `:READ`, и Intervals отвечает `400 invalid_request` (в локальном моке — `Duplicate scope`). Календарная синхронизация (2026-10-02) добавила вторую пару, поэтому ломается и ручная вставка ссылки (`logs/connect-attempt.log`, раздел 2). Сообщение `Duplicate scope` в логах не зафиксировано: там только `invalid_request`. Это следует из воспроизведения на моке, а не из ответа реального Intervals.

3. **Соединение помечалось истёкшим через час — это наш код, а не Intervals.**
   Ответ Intervals не содержит ни `refresh_token`, ни `expires_in` (`logs/connect-attempt.log`, раздел 3). Сервер подставлял `DEFAULT_TOKEN_TTL = 3600` и фоновый `refresh_tokens` помечал соединение `expired, reconnect`, как только срок «выходил», хотя `refresh_token` не было. Для Rivera это совпадает по времени: подключён в 17:41, помечен в 18:37. Токен у Intervals при этом, скорее всего, был жив: Rivera ничего не отзывал, и тикет #219 это подтверждает.

4. **Повторное подключение после истечения ломалось тем же 401.** Следствие пункта 1, а не отдельная ошибка.

## Что изменено

- `static/app.js`: кнопка `<button id="connect">`. По клику делается `POST /api/intervals/auth/init` с токеном, из ответа берётся `authorize_url`, и `window.location.assign(authorize_url)`.
- `server.py`:
  - `/api/intervals/auth/init` перенесён в `do_POST` и возвращает JSON `{authorize_url}` вместо 302. GET больше не обрабатывается (404).
  - `store_connection`: убраны `DEFAULT_TOKEN_TTL`, `expires_at`, `refresh_token` и фоновый поток `refresh_tokens`. Токен живёт, пока атлет его не отзовёт.
  - `wellness()`: на 401 от Intervals токен сбрасывается, статус становится `expired, reconnect`, ответ 409 с текстом «intervals connection expired, reconnect». Так работает ленивая проверка отзыва.
- `config.py`: `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`; удалён `REFRESH_INTERVAL`.

## Что проверено

Локальный мок Intervals (`/tmp/h-Q8IX6v/mock_intervals.py`, подключается через `INTERVALS_BASE`). Мок повторяет формы ответов из логов: `Duplicate scope` на authorize, токен без `refresh_token` и `expires_in`, 401 для отозванных токенов.

- До правок: GET init по ссылке без заголовка даёт 401 (как в логах). Authorize с текущим scope даёт 400 `Duplicate scope`.
- После правок:
  - `POST /auth/init` без токена даёт 401, с токеном даёт JSON с `authorize_url`. GET даёт 404.
  - Цепочка authorize → callback → `/?connected=1` проходит, статус `connected`, scope без дублей, `wellness` отдаёт 200.
  - После отзыва приложения `wellness` даёт 409 `expired, reconnect`, статус `expired, reconnect`. Повторный `POST init` работает.
  - `py_compile` и `node --check` проходят.
- Таймер истечения убран по коду: в `server.py` больше нет `expires_at`, `DEFAULT_TOKEN_TTL` и фонового потока. Ждать час на реальном аккаунте я не стал.

## Что не проверено и что нужно сделать

- Реальный Intervals.icu из этой среды недоступен. Все выводы про поведение провайдера взяты из логов и из мока. Перед выкатом пройти подключение реальным аккаунтом и проверить, что authorize больше не отвечает 400.
- `redirect_uri` в `config.py` не менял. Он должен совпадать с зарегистрированным у Intervals.
- Прод-окружение с настоящими `CLIENT_ID`/`CLIENT_SECRET` не трогал. Ничего не деплоил, не коммитил и никуда не отправлял.

## Заметка коллеги: что пригодилось, что нет

Пригодилось:
- **Правило scope**: каждая область один раз, `:WRITE` без `:READ` для той же области. Это прямо закрыло причину 2.
- **Init как authenticated POST с JSON `authorize_url`** и `window.location.assign`. Это прямо закрыло причину 1.
- **Токен без `refresh_token`, отзыв ловится лениво на первом 401**, без refresh-машинерии. Это закрыло причину 3.

Не пригодилось или не сделано:
- **`state` как JWT с `purpose` и account-mismatch guard.** Текущий `state` уже подписан HMAC и имеет TTL 900 с. Перевод на JWT не даёт выигрыша для этой проблемы, поэтому не делал. Guard на несовпадение `athlete.id` при переподключении — разумное усиление, но вне текущего scope.
- **Упрощение token exchange** (без `grant_type` и `redirect_uri`). В логе от 2026-09-19 обмен с этими полями прошёл успешно, поэтому менять его без проверки на реальном Intervals не стал.
- **`SETTINGS:WRITE`** из примера коллеги. Приложению он не нужен, добавлять не стал.
- **Шифрование токенов at rest.** В текущем коде хранилище в памяти, и этот пункт остаётся открытым до перехода на прод-БД.
