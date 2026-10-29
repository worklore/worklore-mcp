# Причины неполадок интеграции с Intervals.icu

В ходе расследования инцидентов и анализа логов (`logs/connect-attempt.log`, `logs/support-tickets.md`) были выявлены три ключевые проблемы:

---

### 1. Ошибка 401 Unauthorized при нажатии на кнопку «Connect Intervals.icu»

* **Причина:**
  В интерфейсе SPA (`static/app.js`) кнопка подключения была обычной ссылкой:
  ```html
  <a class="btn" href="/api/intervals/auth/init">Connect Intervals.icu</a>
  ```
  При клике браузер выполнял стандартный прямой переход по ссылке (document navigation). При этом заголовок авторизации `Authorization: Bearer <token>`, хранящийся в `localStorage` SPA, не передавался браузером.
  Эндпоинт `/api/intervals/auth/init` требует обязательной авторизации пользователя (`require_user()`), из-за чего сервер возвращал `401 Unauthorized`.
* **Решение:**
  - В SPA (`static/app.js`) кнопка заменена на `<button id="connect">`, клик по которой делает вызов через функцию `api("/api/intervals/auth/init")` с заголовком `Authorization: Bearer ...`.
  - В бэкенде (`server.py`) эндпоинт `auth_init` при обращении с заголовком `Accept: application/json` возвращает JSON с URL для редиректа (`{"url": auth_url}`), после чего клиент перенаправляет браузер на страницу авторизации Intervals.icu (`window.location.href = data.url`).

---

### 2. Ошибка 400 Bad Request (`invalid_request`) на стороне Intervals.icu при открытии ссылки авторизации

* **Причина:**
  В конфигурации скоупов (`config.py`) было указано:
  ```python
  SCOPES = "ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE"
  ```
  В OAuth 2.0 провайдера Intervals.icu действуют строгие правила валидации скоупов:
  1. Скоуп права на запись (`:WRITE`) автоматически включает право на чтение (`:READ`).
  2. Запрещены дублирующие/избыточные скоупы в запросе (например, указание одновременно `ACTIVITY:READ` и `ACTIVITY:WRITE`, или `CALENDAR:READ` и `CALENDAR:WRITE` приводит к ошибке `Duplicate scope` / `invalid_request`).
* **Решение:**
  - В `config.py` список скоупов приведен к корректному виду без дублирования:
  ```python
  SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"
  ```

---

### 3. Сброс подключения через 1 час («Status: expired, reconnect»)

* **Причина:**
  В ответе Intervals.icu на обмен кода (`/api/oauth/token`) отсутствуют поля `expires_in` и `refresh_token`, поскольку OAuth-токены Intervals.icu являются бессрочными (perpetual tokens) и действуют до тех пор, пока пользователь вручную не отзовет доступ в настройках Intervals.icu.
  В коде `server.py`:
  - Функция `store_connection` при отсутствии `expires_in` устанавливала дефолтный тайм-аут жизни токена:
    ```python
    expires_in = int(tok.get("expires_in") or DEFAULT_TOKEN_TTL) # 3600 секунд (1 час)
    ```
  - Фоновый процесс `refresh_tokens()` каждые 60 секунд проверял срок действия токена. Ровно через час (когда до `expires_at` оставалось менее 300 секунд), процесс видел отсутствие `refresh_token` и принудительно переводил статус в:
    ```python
    status = "expired, reconnect"
    ```
* **Решение:**
  - В `server.py` отключена установка искусственного таймера истечения для токенов без `expires_in` (для Intervals.icu `expires_at = None`).
  - Фоновый планировщик обновления `refresh_tokens()` игнорирует токены, у которых нет даты истечения.
  - Добавлена ленивая обработка недействительных токенов: статус меняется на `expired, reconnect`, если реальный запрос к API Intervals.icu (`/wellness`) возвращает `401 Unauthorized` (когда пользователь действительно отозвал доступ).
