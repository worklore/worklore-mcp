# Intervals.icu: почему не подключались и что исправлено

## Причины

1. **Кнопка Connect не работает ни у кого (ticket #214).** Кнопка была `<a href="/api/intervals/auth/init">`,
   то есть обычная навигация GET. Полноэкранный переход не несёт заголовок `Authorization`, которым SPA
   авторизует запросы (`logs/connect-attempt.log`, пункт 1). Сервер отвечал 401 `{"error": "unauthorized"}`.

2. **Ссылка на авторизацию отдавала 400 с 2026-10-02 (ticket #219, пункт 3 лога).** `SCOPES` содержали
   одну и ту же область дважды: `ACTIVITY:READ,ACTIVITY:WRITE` и `CALENDAR:READ,CALENDAR:WRITE`.
   `:WRITE` уже включает `:READ`. Рабочее подключение Rivera было со scope
   `ACTIVITY:WRITE,WELLNESS:READ`, без дублей. Это совпадает с ошибкой «Duplicate scope» из заметки коллеги,
   но на живом Intervals я это не проверял (см. ниже).

3. **Подключение «протухло» через час (ticket #219, пункт 40 лога).** Intervals не отдаёт ни `refresh_token`,
   ни `expires_in`. Сервер подставлял `DEFAULT_TOKEN_TTL = 3600` и без `refresh_token` помечал подключение
   как `expired, reconnect`. Токен на самом деле бессрочный, пока его не отзовёт сам атлет.

4. **Сброс подключения при отзыве не работал.** Если токен отозван в Intervals, wellness возвращал 401,
   но подключение оставалось `connected` и никто не просил переподключиться.

## Что изменено

- `static/app.js`: кнопка стала `<button id="connect">`. По клику она делает `POST /api/intervals/auth/init`
  через обычный `api()`-враппер (с `Authorization`) и переходит на полученный `authorize_url`.
- `server.py`, `auth_init`: маршрут перенесён с GET на POST, ответ `{"authorize_url": ...}` вместо 302.
  GET `/api/intervals/auth/init` теперь отдаёт 404.
- `config.py`: `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`. Каждая область указана один раз.
  `ACTIVITY:READ` и `CALENDAR:READ` убраны, так как их покрывают `:WRITE`.
- `server.py`, `store_connection`: без `expires_in` `expires_at = None`, токен не истекает по таймеру.
  В логе: `connected as athlete ... (no expiry, valid until revoked)`.
- `server.py`, `refresh_tokens`: пропускает подключения с `expires_at = None`. Ветка с обновлением токена
  для провайдеров, которые сообщают `expires_in`, сохранена.
- `server.py`, `wellness`: при 401 от Intervals токен сбрасывается, статус становится `expired, reconnect`,
  ответ 409. Интерфейс покажет «Status: expired, reconnect» и кнопку Connect.

## Что проверено

- `python3 -m py_compile server.py config.py` проходит.
- Сквозной прогон на моке Intervals (через `INTERVALS_BASE`, порт 9999), сервер на порту 8767:
  - `GET /api/intervals/auth/init` даёт 404;
  - `POST` даёт 200 с `authorize_url`, в нём scope `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`;
  - callback с `code` и `state` даёт 302 на `/?connected=1`;
  - `status` показывает `connected`, `wellness` возвращает 200 с данными;
  - после отзыва на моке `wellness` даёт 409, `status` даёт `expired, reconnect`;
  - неавторизованный `POST` даёт 401.
- `node --check static/app.js` проходит.

## Что не проверено и что нужно сделать

- **Живой Intervals.icu не проверялся.** Нет реальных `client_id` и `client_secret`, а `config.py` содержит
  заглушки. Подтверждение, что Intervals принимает новый scope и не отвечает `Duplicate scope`, требует
  одного запроса на `/oauth/authorize` с реальным клиентом.
- **Порт 8766 занят другим процессом** (PID 88629, `server.py` из `/private/tmp/h-kKlOSc`). Я его не трогал.
  Тесты шли на порту 8767. Если он ваш, остановите его и перезапустите сервер, иначе увидите старый код.
- **Уже подключённые атлеты.** Их сохранённый scope старый. После деплоя им нужно нажать Connect ещё раз.
- `APP_SECRET` в `config.py` остаётся заглушкой для разработки. В проде его нужно брать из окружения.

## Что взято из заметки коллеги

- **Пункт 1 (нет refresh_token, токен бессрочный, сброс по 401):** применено. Это главная причина
  «протухания» Rivera.
- **Пункт 2 (scope, каждая область один раз):** применено. Это причина 400.
- **Пункт 4 (init должен быть POST, а не GET-ссылкой):** применено. Это причина 401 на кнопке.
- **Пункт 3 (обмен токена «standard-lite»):** не применено. В логе обмен с `grant_type` и `redirect_uri`
  прошёл успешно и вернул `athlete`, значит поля не мешают. Менять без необходимости не стал.
- **Подпись state с purpose-claim и guard по athlete id:** не применено. Текущая HMAC-подпись state уже
  содержит TTL 15 минут и проверку подписи. Guard на смену athlete id при переподключении стоит добавить
  отдельно, если понадобится.
