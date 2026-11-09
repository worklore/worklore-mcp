# Причины сбоя

1. **Кнопка Connect вела на аутентифицированный GET-эндпоинт обычной ссылкой.** При полном переходе страницы браузер не добавляет заголовок `Authorization`, который SPA передаёт только через `fetch`. Поэтому `/api/intervals/auth/init` получал запрос без пользователя и возвращал 401 всем атлетам. Это подтверждают `logs/connect-attempt.log` и тикет #214.
2. **В authorize URL дублировались области scope.** `ACTIVITY:WRITE` уже включает чтение activity, а `CALENDAR:WRITE` — чтение calendar; одновременные `ACTIVITY:READ,ACTIVITY:WRITE` и `CALENDAR:READ,CALENDAR:WRITE` Intervals.icu отклоняет до показа consent screen. Это объясняет HTTP 400 `invalid_request` после добавления calendar sync.
3. **Бессрочный access token ошибочно считался истекающим через час.** Intervals.icu не возвращает ни `refresh_token`, ни `expires_in`. Код подставлял TTL 3600 секунд, а фоновая задача затем удаляла токен и ставила статус `expired, reconnect`. Именно это произошло с T. Rivera, хотя доступ в Intervals.icu не был отозван.

Дополнительно обмен кода содержал лишние для Intervals.icu поля `grant_type` и `redirect_uri`. В логах нет подтверждения, что они уже вызвали отказ, но формат запроса приведён к фактическому API провайдера.

# Исправления

- `POST /api/intervals/auth/init` теперь требует Bearer-аутентификацию и возвращает `{authorize_url}`. Старый GET-маршрут убран.
- Кнопка в `static/app.js` вызывает init через `fetch`, затем выполняет `window.location.assign(authorize_url)`, поэтому заголовок авторизации не теряется.
- Scope сокращён до `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`, без повторения областей.
- Callback по-прежнему доступен без Bearer-заголовка и проверяет подписанный `state` с TTL 15 минут до обмена кода. Добавлен отказ при попытке заменить сохранённый аккаунт на другой athlete id.
- Token exchange отправляет только `client_id`, `client_secret` и `code`.
- Искусственный TTL, refresh token и фоновой refresher удалены. Access token хранится до отключения или отзыва.
- При 401 от Intervals.icu wellness-клиент очищает access token и переводит соединение в `revoked, reconnect`, вместо продолжения запросов с недействительным токеном.

# Что пригодилось из заметки коллеги

Использованы все четыре описанные особенности: бессрочный токен без refresh-механики и ленивая обработка 401; запрет повторяющихся scope; сокращённый формат token exchange с использованием `athlete.id`; POST init с JSON и переход через `window.location.assign`. Также применена рекомендация проверять athlete id при повторном подключении.

Существующий `state` уже решал задачу идентификации callback: он подписан HMAC, содержит user id и имеет TTL 15 минут, поэтому замена на JWT не потребовалась. Шифрование постоянного хранилища в этом репозитории не менялось: здесь используется только in-memory dev store, а реализация production-хранилища отсутствует.

# Проверка

Выполнен локальный сквозной прогон с HTTP-имитатором Intervals.icu: отказ неавторизованного init, POST init, корректные scope и `state`, callback без Bearer-заголовка, точные поля token exchange, подключённый статус, wellness и очистка токена после имитированного отзыва (401). Также пройдены синтаксические проверки Python и `node --check static/app.js`.

Внешние запросы не выполнялись; проверка с реальным аккаунтом Intervals.icu не проводилась.
