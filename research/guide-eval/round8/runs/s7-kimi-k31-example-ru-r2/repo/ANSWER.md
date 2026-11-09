# Причины сбоя и исправление

## Причины

1. **Кнопка Connect не отправляла авторизацию tricoach.** Она была ссылкой на `GET /api/intervals/auth/init`. При полноценном переходе браузера заголовок `Authorization` из fetch-обёртки SPA не добавляется, поэтому endpoint отвечал `401 Unauthorized`. Это подтверждается `logs/connect-attempt.log` и тикетом #214.
2. **Строка scope содержала повторяющиеся области.** `ACTIVITY:READ,ACTIVITY:WRITE` и `CALENDAR:READ,CALENDAR:WRITE` одновременно запрашивали чтение и запись одной области. Intervals.icu отклоняет такой запрос до показа consent screen; это объясняет ошибку authorize-запроса после добавления calendar sync.
3. **Бессрочный токен искусственно истекал через час.** Intervals.icu не вернул ни `refresh_token`, ни `expires_in`, но код подставлял TTL 3600 секунд. Фоновая задача затем удаляла рабочий access token и ставила статус `expired, reconnect`. Именно это произошло с T. Rivera; отзыва доступа на стороне Intervals не было.
4. **Token exchange не соответствовал варианту OAuth Intervals.icu.** Запрос содержал лишние `grant_type` и `redirect_uri`. Теперь отправляются только `client_id`, `client_secret` и `code`.

## Что изменено

- `POST /api/intervals/auth/init` требует авторизацию и возвращает `{authorize_url}`; старый GET удалён.
- Кнопка в `static/app.js` вызывает init через fetch с `Authorization`, затем выполняет `window.location.assign(authorize_url)`. Ошибка запуска показывается на карточке, кнопку можно нажать повторно.
- Scope заменён на `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`: каждая область указана один раз, а `:WRITE` включает нужное чтение.
- Access token хранится без выдуманного срока действия; фоновый refresher удалён.
- Callback проверяет подпись, назначение (`intervals_oauth`) и 15-минутный TTL state. Добавлена защита от смены athlete id при повторном подключении.
- При первом `401` от Intervals API токен очищается, статус меняется на `revoked, reconnect`, а интерфейс снова предлагает подключение.

## Какие части заметки коллеги пригодились

Пригодились все четыре описанные особенности: бессрочный токен без refresh и lazy-обработка отзыва; запрет дублирования scope; точный набор полей token exchange и использование `athlete.id` из ответа; POST init с JSON и переход через `window.location.assign`. Также использованы рекомендации о назначении и TTL state и о защите от другого athlete id при reconnect.

Готовый HMAC-подписанный state уже обеспечивал перенос user id и TTL, поэтому заменять его именно на JWT не потребовалось: добавлена проверка `purpose`, сохранены подпись и срок действия. Шифрование при хранении в этом прототипе не менялось, поскольку соединения находятся только в памяти и отдельного постоянного хранилища здесь нет.

## Проверка

Локальная имитация Intervals.icu подтвердила полный цикл: POST init, проверка state, callback и token exchange с точным набором полей, статус подключения, wellness с Bearer token, защита от смены аккаунта, переход в `revoked, reconnect` после 401 и disconnect. Отдельная JS-проверка подтвердила POST с `Authorization` и переход по `authorize_url`. Внешние сервисы не вызывались.
