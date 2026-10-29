# Причины и исправления

1. **Connect давал 401 у всех.** Кнопка была ссылкой `<a href=".../auth/init">` на GET-эндпоинт. Полная навигация браузера не отправляет заголовок `Authorization` (он есть только в fetch-обёртке SPA), поэтому сервер отвечал `unauthorized`. Исправлено: `auth/init` теперь аутентифицированный **POST**, возвращает JSON `{authorize_url}`, а SPA делает `fetch` и затем `window.location.assign(authorize_url)` (`server.py`, `static/app.js`). Callback остаётся неаутентифицированным GET; пользователя определяет подписанный `state`.
2. **Authorize отвечал 400 `invalid_request` после 2026-10-02.** В `SCOPES` одни и те же области были указаны дважды (`ACTIVITY:READ,ACTIVITY:WRITE`, `CALENDAR:READ,CALENDAR:WRITE`), а `:WRITE` уже включает `:READ` («Duplicate scope»). Теперь: `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE` (`config.py`).
3. **Подключение «протухало» через час.** Ответ Intervals не содержит `refresh_token` и `expires_in`: токен живёт до отзыва атлетом. Код подставлял TTL 3600 с и фоновым потоком помечал соединение «expired». Убраны `DEFAULT_TOKEN_TTL`, поток-рефрешер и `REFRESH_INTERVAL`. Протухание теперь определяется лениво: при 401 от Intervals токен удаляется, статус становится «revoked, reconnect».

## Какие части заметки пригодились
- Пригодились: п.1 (нет refresh/expiry, ленивая обработка 401), п.2 (Duplicate scope), п.4 (init как POST + JSON, `window.location.assign`, identity через `state`), guard на несовпадение athlete id при повторном подключении (добавлен).
- Не применялись: `SETTINGS:WRITE` в scope (приложению не нужен); урезание обмена кода до `client_id/client_secret/code` — оставлены `grant_type` и `redirect_uri`, т.к. по логам (случай Rivera) обмен с ними успешно проходил; JWT для `state` — оставлен существующий HMAC-state с TTL 15 мин; шифрование токена в БД — в проде, в этом in-memory репозитории не применимо.

Проверка: локально POST `/api/intervals/auth/init` с токеном возвращает `authorize_url` с корректными scope, GET — 404. Реальный OAuth-флоу с Intervals.icu не прогонялся (нет настоящих client_id/secret).
