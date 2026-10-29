# Причины сбоев интеграции с Intervals.icu и внесённые исправления

## 1. Причины проблем

### Проблема 1: Кнопка «Connect» не работает ни у кого (ошибка 401 Unauthorized)
- **Причина:** В SPA ссылка «Connect Intervals.icu» была оформлена как обычный переход по ссылке (`<a href="/api/intervals/auth/init">`), а эндпоинт бэкенда ожидал `GET` с заголовком авторизации `Authorization: Bearer <token>`. При стандартной браузерной навигации по ссылке заголовок `Authorization` (хранящийся в `localStorage`) не передаётся. В результате бэкенд возвращал 401 Unauthorized (`{"error": "unauthorized"}`).

### Проблема 2: Ошибка `invalid_request` (400) от Intervals.icu при открытии ссылки авторизации
- **Причина:** В параметре `scope` в `config.py` были указаны дублирующиеся права доступа для одних и тех же областей:
  `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`.
  В Intervals.icu уровень `:WRITE` автоматически включает `:READ`. Указание обеих областей одновременно приводит к ошибке Intervals.icu («Duplicate scope» / `invalid_request`).

### Проблема 3: Единственный подключившийся пользователь через час перешёл в статус «expired, reconnect»
- **Причина:** Intervals.icu не выдаёт `refresh_token` и `expires_in` — access token является бессрочным до явного отзыва атлетом. В коде `server.py` при отсутствии `refresh_token` токену назначался дефолтный TTL (3600 секунд), а фоновый процесс `refresh_tokens()` через час пытался обновить токен без `refresh_token` и принудительно переводил аккаунт в статус `"expired, reconnect"`, стирая `access_token`.

### Проблема 4: Лишние параметры при обмене кода на токен
- **Причина:** Функция `exchange_code()` отправляла `grant_type: "authorization_code"` и `redirect_uri`, тогда как эндпоинт `POST /api/oauth/token` в Intervals.icu ожидает только `client_id`, `client_secret` и `code`.

---

## 2. Какие части заметки коллеги пригодились

Из заметки коллеги пригодились следующие пункты:
1. **Пункт 1 (Токен никогда не истекает и не обновляется):**
   - Убрали искусственный TTL (3600s) при сохранении токена.
   - Реализовали ленивую обработку отзыва токена: при получении HTTP 401 от Intervals.icu API (`/wellness`) токен сбрасывается, а статус соединения меняется на `"expired, reconnect"`.
2. **Пункт 2 («Duplicate scope»):**
   - Скорректировали `config.SCOPES`, исключив избыточные `:READ` для областей с `:WRITE`: оставили `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.
3. **Пункт 3 (Обмен кода на токен «стандарт-лайт»):**
   - В `exchange_code` убрали `grant_type` и `redirect_uri`, оставив только `client_id`, `client_secret` и `code`.
4. **Пункт 4 (Init-эндпоинт как POST):**
   - Переписали `/api/intervals/auth/init` на аутентифицированный `POST`, возвращающий `{ "authorize_url": ... }` в JSON.
   - Во фронтенде (`app.js`) заменили тег `<a>` на `<button id="connect">`, отправляющий AJAX POST-запрос с заголовком авторизации и выполняющий `window.location.assign(res.authorize_url)`.
   - Дополнительно учли проверку несовпадения аккаунтов атлета (`athlete.id`) при повторном подключении.

---

## 3. Внесённые изменения в кодовой базе

1. **[`config.py`](file:///tmp/h-L3jpPk/config.py):**
   - Заменили строку `SCOPES` на `"ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`.

2. **[`static/app.js`](file:///tmp/h-L3jpPk/static/app.js):**
   - Заменили ссылку `<a href="/api/intervals/auth/init">` на кнопку `<button id="connect">`.
   - Добавили обработчик клика, делающий аутентифицированный `POST /api/intervals/auth/init` через `api()` и перенаправляющий браузер по `res.authorize_url`.

3. **[`server.py`](file:///tmp/h-L3jpPk/server.py):**
   - Перенесли эндпоинт `/api/intervals/auth/init` из `do_GET` в `do_POST`.
   - Метод `auth_init()` теперь возвращает `{"authorize_url": auth_url}` с HTTP 200 вместо `302 Redirect`.
   - В `exchange_code()` убрали лишние поля `grant_type` и `redirect_uri`.
   - В `store_connection()` убрали установку срока истечения и обработку `refresh_token`, добавили валидацию совпадения `athlete_id` при повторном подключении.
   - В `wellness()` добавили обработку HTTP 401 от Intervals.icu с переводом в статус `"expired, reconnect"` и очисткой токена.
