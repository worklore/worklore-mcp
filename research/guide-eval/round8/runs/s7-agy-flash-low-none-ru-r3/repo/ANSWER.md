# Причины сбоев интеграции с Intervals.icu

В ходе расследования инцидентов и анализа логов (`logs/support-tickets.md`, `logs/connect-attempt.log`) были выявлены три независимые причины проблем с подключением аккаунтов Intervals.icu:

---

### 1. Кнопка «Connect Intervals.icu» отдавала ошибку 401 Unauthorized

* **Причина:**
  В интерфейсе (`static/app.js`) кнопка «Connect Intervals.icu» была оформлена как обычная HTML-ссылка `<a href="/api/intervals/auth/init">`. При клике браузер выполнял стандартную навигацию (GET-запрос) по ссылке без заголовка `Authorization: Bearer <token>`, хранящегося в `localStorage`. В бэкенде эндпоинт `/api/intervals/auth/init` требовал авторизации через `require_user()`, проверяя заголовок `Authorization`. Так как заголовок отсутствовал, сервер логично возвращал `401 Unauthorized` (`{"error": "unauthorized"}`).
* **Исправление:**
  - В `static/app.js` ссылка заменена на кнопку `<button id="connect">`, клик по которой делает авторизованный запрос через функцию-обёртку `api("/api/intervals/auth/init")` с заголовком `Authorization: Bearer <token>`. После получения URL авторизации браузер перенаправляется на Intervals.icu (`window.location.href`).
  - В `server.py` метод `auth_init` обновлен: если клиент запрашивает JSON (`Accept: application/json`), сервер возвращает `{"url": auth_url}`, при этом сохранена обратная совместимость (редирект при прямом обращении).

---

### 2. Ошибка `{"error": "invalid_request"}` (400) на стороне Intervals.icu при авторизации

* **Причина:**
  В `config.py` параметр `SCOPES` был настроен следующим образом:
  `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`.
  В OAuth 2.0 провайдере Intervals.icu право `WRITE` автоматически включает в себя соответствующее право `READ`. Если одновременно указать и `READ`, и `WRITE` для одного ресурса (например, `ACTIVITY:READ,ACTIVITY:WRITE` или `CALENDAR:READ,CALENDAR:WRITE`), Intervals.icu считает скоупы дублирующимися/конфликтующими ("Duplicate scope") и отклоняет запрос на авторизацию с ошибкой `400 Bad Request` (`invalid_request`).
* **Исправление:**
  В `config.py` список скоупов приведен к корректному формату без избыточных прав чтения:
  `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.

---

### 3. Сброс подключения через 1 час («Status: expired, reconnect»)

* **Причина:**
  OAuth-токены доступа Intervals.icu являются бессрочными (long-lived) и не имеют механизма `refresh_token` или поля `expires_in` в ответе эндпоинта `/api/oauth/token`. Однако в `server.py`:
  - Функция `store_connection` при отсутствии `expires_in` выставляла принудительный срок жизни токена по умолчанию (`DEFAULT_TOKEN_TTL = 3600` секунд, то есть ровно 1 час).
  - Фоновый поток `refresh_tokens` каждую минуту проверял токены. Когда час подходил к концу, а `refresh_token` в записи отсутствовал (так как Intervals его не предоставляет), сервис автоматически переводил статус подключения в `"expired, reconnect"` и удалял токен:
    ```python
    if not c["refresh_token"]:
        log(f"{uid}: token expiry passed and no refresh token on file -> expired, reconnect")
        c.update(status="expired, reconnect", access_token=None)
    ```
* **Исправление:**
  - В `server.py` в функции `store_connection` поле `expires_at` устанавливается только в том случае, если провайдер явно передал `expires_in` (для токенов Intervals.icu оно остается `None`).
  - Фоновый процесс обновления `refresh_tokens` больше не помечает бессрочные токены (у которых `expires_at is None`) как истекшие.
  - В функцию `intervals_get` добавлена ленивая обработка недействительных токенов: статус переводится в `"expired, reconnect"` только при фактическом получении `401 Unauthorized` от API Intervals.icu (например, если пользователь вручную отозвал доступ в профиле Intervals.icu).
