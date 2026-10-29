# Причины проблем с интеграцией Intervals.icu

В ходе анализа логов (`logs/connect-attempt.log`, `logs/support-tickets.md`) и кодовой базы были выявлены три взаимосвязанные проблемы:

---

### 1. Кнопка «Connect Intervals.icu» не работает ни у кого (ошибка 401 Unauthorized)

* **Причина:**
  В интерфейсе (`static/app.js`) кнопка подключения была реализована как обычная ссылка:
  ```html
  <a class="btn" href="/api/intervals/auth/init">Connect Intervals.icu</a>
  ```
  Токен авторизации пользователя в `tricoach` хранится в `localStorage` и отправляется только JavaScript-оберткой `fetch` через заголовок `Authorization: Bearer <token>`. При обычном переходе по ссылке браузер совершает стандартную навигацию и заголовок `Authorization` не отправляет.
  
  На бэкенде (`server.py`) эндпоинт `/api/intervals/auth/init` вызывал `self.require_user()`, проверявший наличие токена исключительно в заголовке `Authorization`. Из-за его отсутствия сервер возвращал `401 {"error": "unauthorized"}` всем атлетам.

* **Исправление:**
  - В `static/app.js` в ссылку добавлен query-параметр с токеном: `/api/intervals/auth/init?token=${encodeURIComponent(TOKEN)}`.
  - В `server.py` метод `current_user()` дополнен проверкой параметра `token` в строке запроса (query string), если заголовок `Authorization` отсутствует.

---

### 2. Ошибка HTTP 400 `invalid_request` от Intervals.icu при авторизации

* **Причина:**
  После добавления синхронизации календаря в `config.py` были заданы скоупы:
  ```python
  SCOPES = "ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE"
  ```
  В OAuth Intervals.icu разрешения типа `:WRITE` автоматически включают в себя права `:READ`. Передача одновременно дублирующихся областей доступа (`ACTIVITY:READ` вместе с `ACTIVITY:WRITE` и `CALENDAR:READ` вместе с `CALENDAR:WRITE`) расценивается Intervals.icu как дублирование скоупов и отклоняется на шаге авторизации с ошибкой `HTTP 400 {"error": "invalid_request"}` ещё до показа consent screen.

* **Исправление:**
  В `config.py` удалены избыточные `:READ` для областей, где запрошен `:WRITE`:
  ```python
  SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"
  ```

---

### 3. Сброс подключения через 1 час (статус `expired, reconnect`)

* **Причина:**
  Токены доступа Intervals.icu OAuth являются бессрочными (perpetual). Ответ эндпоинта `POST /api/oauth/token` не содержит полей `expires_in` и `refresh_token`. Токен остается валидным до тех пор, пока атлет сам не отзовет доступ в настройках своего аккаунта Intervals.icu.
  
  Однако в `server.py` была жестко задана константа `DEFAULT_TOKEN_TTL = 3600` секунд. Функция `store_connection()` при отсутствии `expires_in` в ответе провайдера устанавливала срок жизни токена ровно в 1 час (`expires_at = time.time() + 3600`).
  
  Фоновый поток `refresh_tokens()` каждые 60 секунд проверяет соединения, у которых `expires_at - now <= 300` (т.е. за 5 минут до истечения). Обнаружив, что у соединения подходит к концу срок действия, а `refresh_token` отсутствует, поток принудительно переводил статус в `"expired, reconnect"` и удалял `access_token`.

* **Исправление:**
  - Убран дефолтный 3600-секундный TTL. Если провайдер не возвращает `expires_in`, поле `expires_at` устанавливается в `None`.
  - Фоновый воркер `refresh_tokens()` теперь пропускает соединения без установленного `expires_at`.
  - Обработка недействительных/отозванных токенов переведена на реактивную (lazy) модель: если при запросе к API Intervals.icu (`/wellness`) возвращается HTTP 401 Unauthorized, соединение помечается как `"expired, reconnect"`.
