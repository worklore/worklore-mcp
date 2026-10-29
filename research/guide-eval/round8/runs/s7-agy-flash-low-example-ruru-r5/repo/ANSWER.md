# Причины проблем с интеграцией Intervals.icu и их исправление

## Причины проблем

1. **Кнопка «Connect Intervals.icu» не работала ни у кого (ошибка 401 Unauthorized)**:
   - В интерфейсе ([static/app.js](file:///tmp/h-Sg0SzC/static/app.js)) кнопка подключения была реализована как обычная ссылка `<a href="/api/intervals/auth/init">`.
   - При обычном переходе по ссылке (полной навигации страницы браузером) заголовок `Authorization: Bearer <token>`, хранящийся в `localStorage` SPA, не отправляется на сервер.
   - Эндпоинт `/api/intervals/auth/init` требует аутентификации пользователя (`require_user()`), поэтому при отсутствии заголовка `Authorization` сервер сразу возвращал `401 {"error": "unauthorized"}`.

2. **Ошибка `invalid_request` (HTTP 400 / Duplicate scope) при открытии authorize URL**:
   - В [config.py](file:///tmp/h-Sg0SzC/config.py) строка `SCOPES` была задана как `"ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE"`.
   - В OAuth API Intervals.icu права `:WRITE` неявно включают права `:READ`, а повторение одного и того же scope (например, `ACTIVITY:READ,ACTIVITY:WRITE` и `CALENDAR:READ,CALENDAR:WRITE`) приводит к ошибке `Duplicate scope` (`invalid_request`) ещё до отображения экрана согласия.

3. **Сброс подключения через час у единственного подключённого атлета («expired, reconnect»)**:
   - Токены доступа Intervals.icu не имеют механизма обновления (`refresh_token`) и срока жизни (`expires_in`) в теле ответа — они действуют бессрочно до тех пор, пока атлет сам не отзовет доступ в настройках Intervals.icu.
   - В коде сервера ([server.py](file:///tmp/h-Sg0SzC/server.py)) при отсутствии `expires_in` и `refresh_token` токену ошибочно назначался искусственный TTL в 3600 секунд (`DEFAULT_TOKEN_TTL`), а фоновый воркер `refresh_tokens()`, видя отсутствие `refresh_token` при приближении к истечению часа, переводил статус подключения в `"expired, reconnect"` и стирал токен.

## Что было исправлено

1. **Инициализация OAuth переведена на POST**:
   - В [server.py](file:///tmp/h-Sg0SzC/server.py) эндпоинт `/api/intervals/auth/init` переведён из `do_GET` в `do_POST` и возвращает JSON `{ "authorize_url": ... }`.
   - В [static/app.js](file:///tmp/h-Sg0SzC/static/app.js) ссылка заменена на кнопку `<button>`, которая вызывает `api("/api/intervals/auth/init", { method: "POST" })` с заголовком авторизации пользователя через fetch-обёртку, а затем перенаправляет пользователя через `window.location.assign(res.authorize_url)`.

2. **Исправлен список SCOPES в [config.py](file:///tmp/h-Sg0SzC/config.py)**:
   - `SCOPES` изменён на `"ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`. Дублирующиеся `:READ` для областей, где уже запрошен `:WRITE`, исключены.

3. **Исправлена логика хранения токена и обработки его истечения**:
   - В `store_connection` токен сохраняется бессрочно (`expires_at = None`), исключена установка искусственного таймера в 3600 секунд. Фоновый планировщик больше не помечает токен истекшим.
   - Реализована ленивая обработка отзыва: при получении HTTP 401 от API Intervals.icu в `/api/intervals/wellness` сохранённый токен сбрасывается, а статус переводится в `"expired, reconnect"`.

4. **Очищен запрос обмена кода на токен**:
   - В `exchange_code` удалены лишние поля `grant_type` и `redirect_uri`, оставлены только `client_id`, `client_secret` и `code`.

5. **Добавлена проверка на несовпадение аккаунтов при переподключении**:
   - В `store_connection` добавлена проверка, чтобы при повторном подключении ID атлета Intervals.icu совпадал с ранее сохранённым.

---

## Использованные части из заметки коллеги

- **Пригодилось**:
  - **Пункт 1 (Токен не истекает и не обновляется)**: помог понять, почему аккаунт переходил в статус `expired, reconnect` ровно через 3600 секунд, и направить реализацию на бессрочное хранение токена и обработку его инвалидации по 401 ошибке от API.
  - **Пункт 2 ("Duplicate scope")**: указал на причину ошибки `HTTP 400 invalid_request` при открытии authorize URL из-за одновременного указания `READ` и `WRITE` для `ACTIVITY` и `CALENDAR`.
  - **Пункт 3 (Обмен кода на токен без grant_type и redirect_uri)**: учтён в функции `exchange_code`, передающей только `client_id`, `client_secret` и `code`.
  - **Пункт 4 (Init-эндпоинт через POST)**: указал на причину 401 ошибки при клике на ссылку в браузере (потеря `Authorization`-заголовка при обычной навигации страницы) и правильный паттерн решения (аутентифицированный POST через fetch, возвращающий `authorize_url`).
  - **Защита от несовпадения аккаунтов**: рекомендация проверять соответствие ID атлета при повторном подключении.

- **Не пригодилось / пропущено**:
  - Предложение заменить state на подписанный JWT: в текущем приложении уже реализована собственная подпись параметра state через HMAC-SHA256 (`sign_state` и `verify_state` с TTL 15 минут), которая выполняет ту же роль и полностью совместима с архитектурой приложения.
  - Шифрование токенов при хранении: в кодовой базе проекта хранилище является демонстрационным in-memory словарём (`CONNECTIONS`), постоянной базы данных нет.
