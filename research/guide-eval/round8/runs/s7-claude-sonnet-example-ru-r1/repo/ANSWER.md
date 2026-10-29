# Intervals.icu: почему не подключалось

## Причины
1. **Кнопка Connect не работала ни у кого.** Это была ссылка `<a href=".../auth/init">`, то есть переход по странице (GET). Браузер при таком переходе не отправляет заголовок `Authorization`, который SPA держит в localStorage, поэтому сервер отвечал 401 `{"error":"unauthorized"}` (тикет #214, лог от 14.10).
2. **Authorize-ссылка вручную тоже падала с 400 `invalid_request`.** С 2026-10-02 в scope стояли `ACTIVITY:READ,ACTIVITY:WRITE` и `CALENDAR:READ,CALENDAR:WRITE`. `:WRITE` уже включает `:READ`, а Intervals отвергает повтор области (`Duplicate scope`). Тело ответа не называет параметр. Одну область нужно указывать один раз.
3. **Подключение «протухало» через час (Rivera).** Токен Intervals не истекает и не обновляется: в ответе нет ни `refresh_token`, ни `expires_in` (это видно в логе от 19.09). Наш код подставлял выдуманный TTL 3600 с и фоновый «рефрешер», который через час помечал подключение как expired и стирал рабочий токен. Rivera при этом ничего не отзывал.
4. **Обмен кода не по формату Intervals.** Мы слали `grant_type` и `redirect_uri`, а Intervals ждёт только `client_id`, `client_secret`, `code`.

## Что изменено
- `server.py`: `auth/init` теперь авторизованный **POST**, который возвращает JSON `{authorize_url}`. `static/app.js`: кнопка делает `api(..., POST)` и затем `window.location.assign(authorize_url)`.
- `config.py`: `SCOPES = ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`, без дублей.
- Удалены TTL, `expires_at`, `refresh_token`, фоновый рефрешер и `REFRESH_INTERVAL`. Токен считается бессрочным.
- Отзыв токена обрабатывается лениво: 401 от Intervals на запросе → токен стирается, статус «expired, reconnect».
- Обмен кода сделан в формате Intervals: только `client_id`, `client_secret`, `code`.
- В `state` добавлено поле `purpose=intervals_oauth` (под подписью HMAC, TTL 15 мин как было).
- При повторном подключении callback отклоняется (409), если athlete id отличается от сохранённого.

## Проверка
Локально проверено, что POST `auth/init` с токеном возвращает корректный `authorize_url` без дублей в scope, а GET на этот путь больше не обслуживается. Реальный OAuth-поток против intervals.icu не запускался: у меня нет доступа к внешнему сервису и реальным client_id/secret.

## Что пригодилось из заметки коллеги
- Пункт 1 (нет refresh_token и срока жизни, ленивая обработка 401): использовано, это причина №3.
- Пункт 2 (Duplicate scope): использовано, причина №2.
- Пункт 3 (обмен только с client_id/secret/code): использовано.
- Пункт 4 (init как POST + `window.location.assign`): использовано, причина №1.
- `state` с purpose и guard на несовпадение athlete id: использовано. Вместо JWT оставлен существующий HMAC-state, потому что он уже содержит подпись и TTL. Заводить JWT-зависимость в stdlib-проекте я не стал.
- Скоуп `SETTINGS:WRITE` из заметки не добавлялся: этому приложению он не нужен (оставлены активности, wellness и календарь).
- Шифрование токена в БД: не применимо, хранилище здесь in-memory. В проде токен надо хранить зашифрованным, поскольку он бессрочный.
