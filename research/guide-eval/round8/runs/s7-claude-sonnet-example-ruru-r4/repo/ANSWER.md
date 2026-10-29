# Почему не подключался Intervals.icu

## Причины
1. **Кнопка Connect — это обычная ссылка `<a href>` на GET `/api/intervals/auth/init`.** Переход по ссылке — полная навигация страницы, заголовок `Authorization` (токен лежит в localStorage и добавляется только в fetch-обёртке) не отправляется, сервер отвечает 401 `{"error":"unauthorized"}`. Поэтому не работало ни у кого (тикет #214).
2. **Дублирующиеся scope.** После календарной синхронизации (2026-10-02) в `SCOPES` стало `ACTIVITY:READ,ACTIVITY:WRITE,...,CALENDAR:READ,CALENDAR:WRITE`. `:WRITE` уже включает `:READ`, Intervals отвечает на такой запрос 400 `invalid_request` (по логам тело ошибки не называет параметр), так что и ручная вставка ссылки перестала работать.
3. **Выдуманный срок жизни токена.** Токен Intervals не истекает и не имеет `refresh_token`/`expires_in`, но код подставлял `DEFAULT_TOKEN_TTL = 3600`, а фоновый поток через час помечал подключение как «expired, reconnect» (Rivera, тикет #219). Отзыв токена при этом нигде не обрабатывался.
4. Обмен кода отправлял лишние `grant_type` и `redirect_uri` (по заметке Intervals нужны только `client_id`, `client_secret`, `code`).

## Что изменено
- `POST /api/intervals/auth/init` возвращает JSON `{authorize_url}`; в `static/app.js` кнопка делает fetch (с заголовком) и затем `window.location.assign(authorize_url)`. GET-вариант удалён.
- `config.SCOPES = ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE` — каждая область один раз.
- Убраны TTL, поток обновления токенов и `expires_at`; соединение живёт, пока не отозвано. При 401 от Intervals токен очищается, статус становится «expired, reconnect» (ленивая обработка отзыва).
- Обмен кода: только `client_id`, `client_secret`, `code`.
- `state` получил claim `purpose` (`intervals_oauth`), проверяется в callback (TTL 15 мин сохранён); при повторном подключении callback отклоняется (409), если id атлета отличается от сохранённого.

## Что пригодилось из заметки
Пункты 1–4 (токен без refresh/expiry, «Duplicate scope», упрощённый обмен кода, init как POST + JSON), а также `state` с purpose и защита от несовпадения атлета. Не применялось: JWT для state (оставлен существующий HMAC-подписанный state с тем же смыслом и TTL), шифрование токена при хранении (хранилище здесь в памяти; в проде токен нужно шифровать), и проверки с реальным аккаунтом Intervals — их я не запускал, только локально проверил, что init отдаёт JSON с authorize_url и что без заголовка отвечает 401.
