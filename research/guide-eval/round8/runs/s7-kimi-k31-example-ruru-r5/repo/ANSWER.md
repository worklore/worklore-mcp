# Причины сбоя интеграции

1. **Кнопка Connect запускала OAuth через обычную ссылку GET.** При полном переходе браузер не добавляет `Authorization: Bearer`, который SPA передаёт только через `fetch`. Поэтому `/api/intervals/auth/init` отвечал 401 всем пользователям; это подтверждено `logs/connect-attempt.log` от 2026-10-14.
2. **В scope дважды встречались области ACTIVITY и CALENDAR.** Одновременно запрашивались `:READ` и `:WRITE`, хотя `:WRITE` уже включает чтение. Intervals.icu отклонял authorize-запрос до показа экрана согласия; это объясняет `invalid_request` от 2026-10-17 и поломку после добавления calendar sync.
3. **Отсутствие `expires_in` ошибочно трактовалось как срок жизни 3600 секунд.** Фоновый refresher через час удалял access token, если не было `refresh_token`, хотя Intervals.icu выдаёт бессрочный токен без механизма refresh. Поэтому подключение Rivera's было помечено `expired, reconnect`, несмотря на отсутствие отзыва.
4. **Обмен кода содержал лишние поля `grant_type` и `redirect_uri`.** Это ещё одно несоответствие OAuth API Intervals.icu; теперь отправляются только `client_id`, `client_secret` и `code`.

# Что исправлено

- Connect стал кнопкой: SPA делает аутентифицированный `POST /api/intervals/auth/init`, получает `{authorize_url}` и переходит по нему через `window.location.assign`. Прежний GET-маршрут убран.
- Scope сокращён до `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE` без повторов.
- Удалены выдуманный TTL, поля refresh/expiry и фоновый refresher. Access token остаётся действующим до отзыва.
- При 401 от Intervals API сохранённый токен очищается, статус меняется на `revoked, reconnect`, после чего доступно повторное подключение.
- В подписанный `state` добавлен `purpose: intervals_oauth`; сохранена проверка HMAC и TTL 15 минут. При повторном подключении другого athlete callback отклоняется, не заменяя существующее подключение.
- Из token response по-прежнему используются `access_token`, `scope` и `athlete`; `refresh_token` больше не ожидается.

# Какие части заметки пригодились

Пригодились все четыре описанные особенности: отсутствие refresh/expiry и ленивая обработка отзыва по 401; правило не дублировать scope; точный набор полей token exchange и данные `athlete`; POST init с JSON вместо GET-ссылки. Также использованы рекомендации о `purpose` и TTL в `state` и защите от смены athlete при повторном подключении.

Совет о шифровании при постоянном хранении здесь не потребовал изменений: этот проект хранит подключения только в памяти и не имеет постоянного хранилища. JWT не внедрялся — существующий подписанный HMAC-формат уже обеспечивает нужную проверку без новой зависимости.

# Проверка

- `python3 -m py_compile server.py config.py` и `node --check static/app.js` — успешно.
- Полный поток проверен через локальный HTTP-имитатор Intervals.icu: auth init, callback, точные поля token exchange, status, wellness, несовпадение athlete, отзыв 401 и reconnect — успешно.
- К внешнему Intervals.icu не обращался: реальные OAuth client credentials и аккаунт для такого прогона в проекте не заданы, а обращения к внешним сервисам были запрещены.
