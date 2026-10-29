# Причины проблем с интеграцией Intervals.icu

В ходе анализа логов (`logs/connect-attempt.log`), обращений атлетов (`logs/support-tickets.md`) и исходного кода приложения были выявлены три ключевые проблемы:

---

### 1. Ошибка 401 Unauthorized при клике на кнопку «Connect Intervals.icu»
* **Причина:**
  В интерфейсе (`static/app.js`) кнопка «Connect Intervals.icu» была оформлена как обычная HTML-ссылка `<a href="/api/intervals/auth/init">`. При обычном клике/переходе по ссылке браузер выполняет стандартную навигацию документа и не передает заголовок авторизации `Authorization: Bearer <token>`. Эндпоинт `/api/intervals/auth/init` требует аутентификации (`require_user()`), из-за чего сервер возвращал ошибку `401 Unauthorized` (`{"error": "unauthorized"}`).
* **Исправление:**
  - В `static/app.js` ссылка заменена на интерактивную кнопку с обработчиком клика. Обработчик вызывает `/api/intervals/auth/init` через SPA-обертку `api()`, которая автоматически прикрепляет токен пользователя в заголовке `Authorization: Bearer ...`.
  - В `server.py` метод `auth_init` теперь проверяет заголовок `Accept`: если запрос отправлен как JSON, сервер возвращает JSON с URL редиректа (`{"url": "..."}`), после чего клиент перенаправляет пользователя на страницу авторизации Intervals.icu (`window.location.href`).

---

### 2. Ошибка 400 `{"error": "invalid_request"}` со стороны Intervals.icu при запросе прав (scope)
* **Причина:**
  В `config.py` были указаны скоупы:
  `SCOPES = "ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE"`
  В API Intervals.icu права уровня `:WRITE` автоматически включают в себя права `:READ`. Передача одновременно дублирующих/конфликтующих скоупов (например, `ACTIVITY:READ` вместе с `ACTIVITY:WRITE` или `CALENDAR:READ` вместе с `CALENDAR:WRITE`) приводит к отклонению запроса сервером авторизации Intervals.icu с ошибкой `400 invalid_request` еще до отображения экрана согласия (consent screen).
* **Исправление:**
  - В `config.py` скоупы приведены к корректному виду без дублирования:
    `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`

---

### 3. Сброс подключения через 1 час («Status: expired, reconnect»)
* **Причина:**
  Токены доступа OAuth в Intervals.icu являются бессрочными (не истекают по таймеру и действуют до тех пор, пока пользователь явно не отзовет доступ в интерфейсе Intervals.icu). Ответ от `/api/oauth/token` не содержит полей `expires_in` и `refresh_token`.
  Однако в `server.py`:
  1. В функции `store_connection` при отсутствии `expires_in` по умолчанию выставлялся TTL в 3600 секунд (`DEFAULT_TOKEN_TTL = 3600`).
  2. Фоновый процесс `refresh_tokens()` каждые 60 секунд проверял токены. Через 55 минут (когда до истечения оставалось <= 300 секунд) он обнаруживал отсутствие `refresh_token` и принудительно переводил статус подключения в `"expired, reconnect"`, стирая `access_token`.
* **Исправление:**
  - В `server.py` логика `store_connection` изменена: если поле `expires_in` отсутствует в ответе от провайдера, время истечения устанавливается в `None` (токен считается бессрочным).
  - В фоновом планировщике `refresh_tokens()` исключены токены с `expires_at is None`.
  - Добавлена ленивая обработка недействительности токена в `wellness()`: если Intervals.icu вернет `401 Unauthorized` (пользователь отозвал права), статус подключения переводится в `"expired, reconnect"`.
