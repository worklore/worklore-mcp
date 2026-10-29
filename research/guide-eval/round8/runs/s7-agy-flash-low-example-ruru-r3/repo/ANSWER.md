# Причины сбоев интеграции с Intervals.icu и внесённые исправления

## 1. Причины проблем

1. **Кнопка «Connect Intervals.icu» не работала ни у кого (ошибка 401 Unauthorized):**
   - В SPA (`static/app.js`) кнопка представляла собой обычную ссылку `<a href="/api/intervals/auth/init">`. При прямом переходе браузера по ссылке (навигация документа) заголовок `Authorization: Bearer <token>`, хранящийся в `localStorage`, не отправляется.
   - Эндпоинт `/api/intervals/auth/init` требовал авторизацию пользователя и при отсутствии заголовка возвращал `401 Unauthorized` (`{"error": "unauthorized"}`).

2. **Ошибка `invalid_request` (Duplicate scope) на стороне Intervals.icu:**
   - В `config.py` была настроена строка `SCOPES = "ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE"`.
   - В Intervals.icu права `:WRITE` неявно включают `:READ`, а указание обеих областей одновременно (`ACTIVITY:READ,ACTIVITY:WRITE` и `CALENDAR:READ,CALENDAR:WRITE`) вызывает ошибку валидации скоупов (`Duplicate scope` / `invalid_request`), из-за чего атлетам даже не показывался экран согласия.

3. **Почему атлета через час попросили подключиться заново:**
   - В ответе OAuth Intervals.icu (`POST /api/oauth/token`) отсутствуют поля `refresh_token` и `expires_in` — выданный токен бессрочный и действует до тех пор, пока пользователь сам не отзовёт его в интерфейсе Intervals.icu.
   - В бэкенде (`server.py`) при отсутствии `expires_in` устанавливался тайм-аут по умолчанию `DEFAULT_TOKEN_TTL = 3600` секунд (1 час). Фоновый поток `refresh_tokens()` пытался обновить токен через 1 час, но поскольку `refresh_token` не был получен от провайдера, поток переводил статус подключения в `"expired, reconnect"` и обнулял `access_token`.

4. **Лишние параметры в запросе обмена кода на токен:**
   - В `exchange_code()` отправлялись `grant_type: "authorization_code"` и `redirect_uri`. Intervals.icu ожидает только `client_id`, `client_secret` и `code`.

---

## 2. Какие части из заметки коллеги пригодились

Из предложенной заметки пригодились следующие пункты:

- **Пункт 1 (Токен не истекает и нет refresh_token):**
  Полностью пригодился. Убрали ошибочную логику истечения токена через 1 час и фоновый поток обновления `refresh_tokens()`, который ошибочно помечал токен как `"expired, reconnect"`. Добавлена ленивая обработка отзыва: статус меняется на `"expired, reconnect"`, если Intervals.icu возвращает 401 на запросы к API (например, `/api/intervals/wellness`).

- **Пункт 2 ("Duplicate scope"):**
  Полностью пригодился. Исправили `SCOPES` в `config.py`, убрав дублирование прав чтения и записи: оставили только `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.

- **Пункт 3 (Обмен кода на токен «стандарт-лайт»):**
  Полностью пригодился. В функции `exchange_code` (`server.py`) запрос сокращён до необходимых полей `client_id`, `client_secret` и `code` (убраны `grant_type` и `redirect_uri`).

- **Пункт 4 (Init-эндпоинт как аутентифицированный POST + защита от подмены аккаунта):**
  Полностью пригодился. В SPA эндпоинт `/api/intervals/auth/init` теперь вызывается через `POST` с Bearer-токеном с помощью fetch-обёртки, бэкенд возвращает `{authorize_url}`, после чего фронтенд выполняет `window.location.assign(authorize_url)`. Также при повторном подключении добавлена проверка на несовпадение `athlete_id`.

**Что не пригодилось / было пропущено:**
- Механика генерации и валидации `state`: в текущей кодовой базе уже была реализована достаточная подпись HMAC с TTL 15 минут (`sign_state`/`verify_state`), переписывать её на JWT не потребовалось.
