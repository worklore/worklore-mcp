# Исправление интеграции Intervals.icu

## Причины сбоя

1. **Кнопка Connect не отправляла токен аутентификации tricoach.** В `static/app.js` использовалась обычная ссылка на `GET /api/intervals/auth/init`. При полноценном переходе браузер не добавляет `Authorization: Bearer ...`, который SPA передаёт только через `fetch`, поэтому backend отвечал `401 Unauthorized`. Это подтверждается `logs/connect-attempt.log:5-13` и тикетом #214.
2. **Authorize URL содержал дубли scope.** Для `ACTIVITY` и `CALENDAR` одновременно запрашивались `:READ` и `:WRITE`, хотя `:WRITE` уже включает чтение. Intervals отклоняет повтор области (`Duplicate scope`), поэтому после добавления календарных прав запрос не доходил до экрана согласия (`logs/connect-attempt.log:15-30`, тикет #219).
3. **Действующий токен ошибочно удалялся через час.** Intervals не возвращает ни `refresh_token`, ни `expires_in`: access token действует до отзыва спортсменом. Backend подставлял TTL 3600 секунд и фоновой задачей переводил подключение в `expired, reconnect`, хотя отзыва не было (`logs/connect-attempt.log:35-40`). Именно поэтому T. Rivera попросили подключиться заново.

Дополнительно обмен authorization code приведён к варианту Intervals: в `POST /api/oauth/token` отправляются только `client_id`, `client_secret` и `code`, без `grant_type` и `redirect_uri`.

## Что изменено

- Connect теперь является кнопкой: SPA делает аутентифицированный `POST /api/intervals/auth/init`, получает `{authorize_url}` и переходит по нему через `window.location.assign`. Ошибка инициализации показывается на карточке, кнопка при этом снова становится доступной.
- Scope сокращены до `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE` — каждая область указана один раз.
- Удалены искусственный TTL, поля refresh/expiry и фоновый refresher. Access token сохраняется как бессрочный до отзыва.
- При первом `401` от Intervals API сохранённый токен очищается, статус меняется на `revoked, reconnect`, а клиент получает понятную ошибку с предложением переподключиться.
- Подписанный `state` по-прежнему содержит user id и TTL 15 минут; добавлена проверка назначения `intervals_oauth` и отклонение дат из будущего. Формат HMAC сохранён вместо замены на JWT.
- При повторном подключении callback отклоняет другой `athlete.id`, не перезаписывая существующее подключение.
- Из ответа token endpoint используются `access_token`, `scope` и `athlete` для последующих запросов `/api/v1/athlete/{athlete_id}/...`.

## Какие части заметки пригодились

Пригодились все четыре основных наблюдения: отсутствие refresh/expiry и ленивая обработка отзыва через `401`; правило уникальных scope; сокращённый набор полей token exchange и использование `athlete.id`; переход init на аутентифицированный `POST` с JSON и последующим `window.location.assign`. Также применены рекомендации о назначении и TTL `state` и защите от смены athlete account при reconnect.

Заметка не применялась буквально в двух местах: существующий HMAC-подписанный `state` оставлен вместо JWT, а шифрование при хранении не добавлено, потому что этот dev-backend держит подключения только в памяти и не имеет постоянного хранилища. В постоянном production-хранилище такой бессрочный токен нужно шифровать. `SETTINGS:WRITE` из примера коллеги не добавлен: приложению этот доступ не нужен.

## Проверка

- `python3 -m py_compile server.py config.py` и `node --check static/app.js` прошли.
- Полный flow проверен через реальные HTTP-запросы к локальному backend и локальному имитатору Intervals: init, callback, точный набор form-полей, status, wellness с Bearer token, отзыв (`401`), reconnect и account-mismatch guard.
- Обработчик кнопки SPA проверен в Node: отправляет `POST` с `Authorization`, перенаправляет по `authorize_url` и показывает ошибку при неудачном init.

Внешние запросы не выполнялись, поэтому подтверждение на реальном аккаунте Intervals в рамках этой задачи не проводилось.
