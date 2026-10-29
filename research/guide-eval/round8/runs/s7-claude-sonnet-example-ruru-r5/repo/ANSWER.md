# Почему не подключался Intervals.icu — причины и исправления

## Причины
1. **Кнопка Connect (#214).** Это была ссылка `<a href="/api/intervals/auth/init">` на GET-эндпоинт. Полная навигация страницы не отправляет заголовок `Authorization` (токен лежит в localStorage и добавляется только fetch-обёрткой), поэтому сервер отвечал всем 401.
   Исправление: `POST /api/intervals/auth/init` (через `api()`), возвращает JSON `{authorize_url}`; кнопка делает `window.location.assign(...)`.
2. **400 `invalid_request` на authorize.** В scope были и `ACTIVITY:READ`, и `ACTIVITY:WRITE` (и `CALENDAR:READ`+`WRITE`) — Intervals считает это дублем области (`:WRITE` уже включает `:READ`). Новый scope: `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.
3. **Токен «истекал» через час (#219).** Intervals не выдаёт `refresh_token` и `expires_in`; токен бессрочный, пока атлет его не отзовёт. Код подставлял выдуманный TTL 3600 с и фоновый «рефрешер» помечал подключение просроченным. Рефрешер и TTL удалены; отзыв обрабатывается лениво: при 401 от API токен очищается и статус становится «revoked, reconnect».
4. **Обмен кода.** Лишние `grant_type` и `redirect_uri` убраны: нужны только `client_id`, `client_secret`, `code`. Из ответа берутся `access_token`, `scope`, `athlete`.
5. **State.** Добавлен `purpose=intervals_oauth` в подписанный state (TTL 15 мин сохранён). При повторном подключении callback отклоняется (409), если id атлета не совпадает с сохранённым.

## Что пригодилось из заметки коллеги
- Пп. 1–4 заметки (нет refresh_token, Duplicate scope, упрощённый обмен кода, init как POST) — применены, все они совпали с логами.
- State с `purpose` и защита от несовпадения аккаунтов — применено (state оставлен HMAC-подписью, не JWT: существующая схема уже равноценна).
- Не применено: `SETTINGS:WRITE` в scope (приложению не нужен); шифрование токена при хранении — здесь хранилище в памяти, в проде при записи в Postgres токен стоит шифровать; регистрация клиента и реальный аккаунт Intervals — вне этой директории.

## Проверка
Локально: POST init с Bearer возвращает `authorize_url` без дублей scope; GET без заголовка больше не используется. Реальный поток с Intervals.icu не проверялся (нет доступа и реальных client_id/secret).
