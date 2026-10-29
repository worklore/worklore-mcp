# Причины сбоев интеграции с Intervals.icu и исправления

## 1. Выявленные причины проблем

### Причина 1: Кнопка «Connect Intervals.icu» отдавала 401 Unauthorized у всех пользователей
* **Что происходило:** Эндпоинт `/api/intervals/auth/init` был реализован как `GET`, а на фронтенде кнопка являлась обычной ссылкой `<a href="/api/intervals/auth/init">`.
* **Почему ломалось:** При обычном клике по ссылке (document navigation) браузер переходит по URL без заголовка `Authorization: Bearer <token>`, хранящегося в `localStorage` клиентского SPA. Бэкенд справедливо требовал авторизацию и возвращал `401 Unauthorized` с JSON `{"error": "unauthorized"}`.

### Причина 2: Ошибка «Duplicate scope» и HTTP 400 invalid_request при переходе на страницу авторизации
* **Что происходило:** При ручной генерации ссылки с токеном переход на Intervals.icu возвращал ошибку `HTTP 400 invalid_request`.
* **Почему ломалось:** В [config.py](file:///tmp/h-29GNnc/config.py) строка скоупов была настроена как `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`. В Intervals.icu права `:WRITE` неявно включают `:READ`, а указание обеих привилегий для одной и той же области (дублирование областей) расценивается как `Duplicate scope` и отклоняется сервером авторизации.

### Причина 3: Разрыв соединения через 1 час («expired, reconnect») у единственного подключенного атлета
* **Что происходило:** Токен Т. Риверы был помечен как `expired, reconnect` ровно через 3600 секунд (1 час) после успешного подключения, хотя атлет ничего не отзывал в Intervals.icu.
* **Почему ломалось:** В OAuth Intervals.icu `access_token` не имеет срока истечения (`expires_in`) и не возвращает `refresh_token` (токен бессрочный, пока пользователь явно не отзовет его). В коде [server.py](file:///tmp/h-29GNnc/server.py):
  1. При отсутствии `expires_in` токену принудительно назначался дефолтный TTL в 1 час (`DEFAULT_TOKEN_TTL = 3600`).
  2. Фоновый поток `refresh_tokens()` проверял истечение токенов. При наступлении дедлайна он видел отсутствие `refresh_token` и переводил статус подключения в `"expired, reconnect"`, сбрасывая рабочий `access_token`.

### Причина 4: Лишние параметры при обмене кода на токен
* **Что происходило:** В функции `exchange_code` на эндпоинт токенов передавались `grant_type: "authorization_code"` и `redirect_uri`. Intervals.icu OAuth ожидает только `client_id`, `client_secret` и `code`.

---

## 2. Какие части заметки коллеги пригодились

Из заметки коллеги пригодились следующие пункты:

1. **Пункт 1 («The token never expires and never refreshes»):** 
   - **Пригодилось полностью.** Убрали принудительное назначение дефолтного срока жизни для токенов без `expires_in`, отключили сброс подключения фоновым потоком для токенов без refresh-токена, добавили ленивую инвалидацию подключения (сброс в `"expired, reconnect"`) при получении 401 на запросах к API Intervals.icu.

2. **Пункт 2 («Duplicate scope»):** 
   - **Пригодилось полностью.** В конфигурации [config.py](file:///tmp/h-29GNnc/config.py) убрали дублирующие `:READ` для областей, где запрошен `:WRITE`, заменив список скоупов на `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.

3. **Пункт 3 («The token exchange is standard-lite»):** 
   - **Пригодилось.** В вызове `exchange_code` в [server.py](file:///tmp/h-29GNnc/server.py) убрали поля `grant_type` и `redirect_uri`, оставив только `client_id`, `client_secret` и `code`.

4. **Пункт 4 («The init endpoint must be POST»):** 
   - **Пригодилось частично (первая часть):**
     - Перевели эндпоинт `/api/intervals/auth/init` с `GET` на `POST` с возвратом JSON `{authorize_url: ...}`.
     - В [static/app.js](file:///tmp/h-29GNnc/static/app.js) кнопку Connect заменили со ссылки `<a>` на кнопку `<button>`, отправляющую авторизованный `POST`-запрос через обертку `api()` с последующим переходом через `window.location.assign(res.authorize_url)`.
   - **Что пропущено / не требовалось менять:**
     - Подпись `state` через JWT (в текущем коде уже была реализована достаточная HMAC-SHA256 подпись `sign_state` / `verify_state` со временем жизни 15 минут, которая уже корректно валидирует `state` в коллбеке).
     - Guard на несовпадение `athlete_id` при переподключении.

---

## 3. Внесённые изменения в файлы

1. **[config.py](file:///tmp/h-29GNnc/config.py)**:
   - Обновлен `SCOPES`: `"ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"` (без дублирования `:READ` и `:WRITE`).
2. **[server.py](file:///tmp/h-29GNnc/server.py)**:
   - Эндпоинт `/api/intervals/auth/init` переведён в `do_POST` и возвращает `{"authorize_url": authorize_url}`.
   - В `exchange_code` удалены лишние поля `grant_type` и `redirect_uri`.
   - В `store_connection` токен сохраняется бессрочным, если `expires_in` отсутствует.
   - В `refresh_tokens` фоновое обновление не сбрасывает токены без срока действия и без `refresh_token`.
   - В `wellness` добавлен перехват `HTTP 401`, при котором статус подключения переводится в `"expired, reconnect"`.
3. **[static/app.js](file:///tmp/h-29GNnc/static/app.js)**:
   - Кнопка «Connect Intervals.icu» теперь выполняет аутентифицированный `POST /api/intervals/auth/init` с токеном из `localStorage` и выполняет редирект на полученный `authorize_url`.
