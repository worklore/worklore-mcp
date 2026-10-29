# Причины проблем с интеграцией Intervals.icu и исправления

## 1. Выявленные причины проблем

На основе логов (`logs/connect-attempt.log`, `logs/support-tickets.md`) и анализа исходного кода приложения были установлены следующие причины:

1. **Кнопка «Connect Intervals.icu» не работала ни у кого (ошибка 401 Unauthorized)**:
   - В интерфейсе (`static/app.js`) кнопка подключения была реализована в виде обычной HTML-ссылки `<a href="/api/intervals/auth/init">`.
   - При клике по ссылке происходила прямая навигация браузера (`GET /api/intervals/auth/init`), при которой токен авторизации пользователя из `localStorage` (`Authorization: Bearer ...`) не передавался (заголовки передаются только через XHR/fetch).
   - Сервер требовал авторизацию на эндпоинте инициализации (`self.require_user()`) и закономерно возвращал `401 {"error": "unauthorized"}`.

2. **Ручная ссылка для авторизации приводила к 400 Bad Request ("invalid_request") / Duplicate scope**:
   - При добавлении синхронизации календаря в `config.py` была настроена строка скоупов:  
     `SCOPES = "ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE"`.
   - В Intervals.icu права `:WRITE` неявно включают права `:READ`, и дублирование области (например, `ACTIVITY:READ` и `ACTIVITY:WRITE` одновременно) приводит к ошибке авторизации `Duplicate scope` (возвращается как HTTP 400 `invalid_request`).

3. **Единственного атлета (T. Rivera) через час попросили подключиться заново**:
   - Intervals.icu OAuth выдает перманентный access token и **не возвращает** `refresh_token` и `expires_in`.
   - В `server.py` при отсутствии `expires_in` токену назначался искусственный `DEFAULT_TOKEN_TTL = 3600` секунд (1 час).
   - Фоновый процесс `refresh_tokens()` каждые 60 секунд проверял срок действия токенов. Спустя час он обнаружил, что срок действия токена истек, а `refresh_token` отсутствует, и принудительно перевел статус подключения атлета в `"expired, reconnect"`, сбросив `access_token`.

4. **Лишние параметры в обмене кода на токен**:
   - Функция `exchange_code` передавала в `POST /api/oauth/token` параметры `grant_type="authorization_code"` и `redirect_uri`, тогда как эндпоинт Intervals.icu ожидает только `client_id`, `client_secret` и `code`.

---

## 2. Какие части заметки коллеги пригодились

Из заметки коллеги пригодились следующие положения и рекомендации:

1. **Раздел 1 («The token never expires and never refreshes»)**:
   - **Пригодилось полностью**: убрали логику искусственного срока жизни токена (3600 сек) и фоновый цикл `refresh_tokens()`. Токен Intervals.icu не имеет срока давности и не требует обновления по таймеру. Реализована ленивая обработка отзыва: при получении `401 Unauthorized` от API Intervals.icu (в запросах к велнесу/активностям) статус подключения переводится в `"expired, reconnect"`, а токен сбрасывается.

2. **Раздел 2 («"Duplicate scope"»)**:
   - **Пригодилось полностью**: скорректировали строку `SCOPES` в `config.py` на `"ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`, исключив дублирование областей (`ACTIVITY` и `CALENDAR` указаны только с суффиксом `:WRITE`).

3. **Раздел 3 («The token exchange is standard-lite»)**:
   - **Пригодилось полностью**: в `exchange_code` удалили лишние поля `grant_type` и `redirect_uri`, оставив только `client_id`, `client_secret` и `code`.

4. **Раздел 4 («The init endpoint must be POST»)**:
   - **Пригодилось**: перевели эндпоинт `/api/intervals/auth/init` на метод `POST`, возвращающий `{authorize_url: ...}`. В `static/app.js` заменили ссылку на кнопку, отправляющую авторизованный fetch-запрос через функцию `api()` и выполняющую `window.location.assign(res.authorize_url)`.
   - **Проверка mismatch**: добавлена проверка несовпадения `athlete_id` при повторном подключении учетной записи (account-mismatch guard).
   - **Что пропущено / не требовалось менять**: механизм подписи `state` на основе HMAC-SHA256 уже присутствовал в кодовой базе и корректно передавал `user_id` с 15-минутным TTL; переход на стороннюю библиотеку JWT не требовался, текущей реализации `sign_state` / `verify_state` достаточно.
