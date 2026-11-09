# Причины сбоя интеграции Intervals.icu

1. **Кнопка Connect не отправляла токен авторизации tricoach.** Она была обычной ссылкой на `GET /api/intervals/auth/init`. При полностраничном переходе браузер не добавляет `Authorization: Bearer ...`, который SPA передаёт только через `fetch`, поэтому endpoint возвращал 401. Это подтверждено записями от 2026-10-14 в `logs/connect-attempt.log` и тикетом #214.
2. **Authorize URL содержал дублирующиеся области доступа.** В `config.py` одновременно запрашивались `ACTIVITY:READ,ACTIVITY:WRITE` и `CALENDAR:READ,CALENDAR:WRITE`. У Intervals.icu `:WRITE` уже включает `:READ`; повтор области приводит к отказу authorize-запроса (`Duplicate scope`). Это объясняет ошибку 400 до показа consent screen после добавления calendar sync.
3. **Бессрочный access token ошибочно считался действительным один час.** Intervals.icu не возвращает `refresh_token` и `expires_in`: токен действует до отзыва спортсменом. Код подставлял TTL 3600 секунд и фоновая задача удаляла токен, хотя на стороне Intervals.icu он оставался действительным. Это подтверждено журналом подключения T. Rivera от 2026-09-19 и тикетом #219.
4. **Отзыв доступа не обрабатывался как разрыв соединения.** Теперь первый 401 от Intervals API очищает сохранённый токен и переводит соединение в состояние `revoked, reconnect`.

# Исправления

- `static/app.js`: Connect стал кнопкой; SPA делает аутентифицированный `POST /api/intervals/auth/init`, получает `{authorize_url}` и выполняет `window.location.assign(...)`.
- `server.py`: init принимает только POST и возвращает JSON вместо redirect. Callback остаётся публичным GET и по-прежнему проверяет подписанный `state` с TTL 15 минут.
- `config.py`: scopes заменены на `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE` — каждая область указана один раз.
- `server.py`: обмен кода отправляет только `client_id`, `client_secret`, `code`. Удалены выдуманный TTL, refresh token и фоновый refresher; токен хранится до отзыва.
- `server.py`: при 401 от API соединение переходит в reconnect. При повторном подключении callback отклоняет другой athlete id, если аккаунт уже связан с пользователем.

# Что пригодилось из заметки коллеги

Использованы все четыре основных наблюдения: бессрочность токена и lazy reconnect по 401; запрет дублирования scope; формат token exchange с тремя полями и athlete id в ответе; POST init с JSON и переход через `window.location.assign`. Также применён account-mismatch guard.

Существующий HMAC-подписанный `state` уже связывал callback с пользователем и имел TTL 15 минут, поэтому замена на JWT и добавление `purpose` не потребовались. Шифрование at rest не добавлялось: этот проект хранит соединения только в памяти и не содержит слоя постоянного хранения.

# Проверка

Локально, без запросов к внешним сервисам, пройден HTTP-сценарий init → callback → token exchange → status → wellness → 401/reconnect, а также проверен account-mismatch guard. Ответы Intervals.icu были заменены локальными mock-объектами. `python3 -m py_compile server.py config.py`, `node --check static/app.js` и `git diff --check` прошли. Реальный аккаунт Intervals.icu не использовался.
