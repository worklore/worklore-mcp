# Почему не подключался Intervals.icu

Было три независимые причины.

## 1. Кнопка Connect всегда даёт 401 (тикет #214)

Сервер узнаёт пользователя только по заголовку `Authorization: Bearer <token>`.
Этот заголовок добавляет обёртка `api()` в SPA. Токен лежит в `localStorage`,
cookie нет. Но кнопка была обычной ссылкой
`<a href="/api/intervals/auth/init">`. При переходе по ссылке браузер
загружает документ сам, а не через `fetch`, поэтому заголовок `Authorization`
не отправляется. `require_user()` возвращает 401 `{"error":"unauthorized"}`.
В логе это видно: `401 (no Authorization header)`, запрос типа «document
navigation». Так происходило у всех и при каждом нажатии.

**Исправление.** `/api/intervals/auth/init` теперь возвращает JSON `{"url": ...}`
и не делает 302. Кнопка вызывает этот адрес через `api()` (с токеном) и
затем сама выполняет `window.location.href = url`.

## 2. Intervals отвечает 400 `invalid_request` на authorize (с 2026-10-02)

После выхода синхронизации календаря в `SCOPES` стало
`ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`.
В Intervals.icu каждая область (ACTIVITY, WELLNESS, CALENDAR, …) указывается
один раз: `AREA:READ` или `AREA:WRITE`, и WRITE уже включает READ. Если
область указана дважды, authorize-запрос невалиден, и Intervals отклоняет
его до экрана согласия. Об этом говорит и токен Ривера: Intervals выдал
scope `ACTIVITY:WRITE,WELLNESS:READ`, то есть по одному уровню на область.

**Исправление.** `config.SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`.

## 3. Через час после подключения просили переподключиться (тикет #219)

Токены доступа Intervals.icu бессрочные. Они действуют, пока атлет не
отзовёт приложение, поэтому в ответе нет ни `refresh_token`, ни `expires_in`.
В ответе для Ривера их тоже нет. Код подставлял `DEFAULT_TOKEN_TTL = 3600`, и
через час фоновый `refresh_tokens()` видел «истёкший» токен без refresh token.
Он стирал рабочий `access_token` и ставил статус `expired, reconnect`.
Срок действия придумал сам код, а не Intervals. Поэтому приложение и осталось
в списке разрешённых у Ривера на стороне Intervals.

**Исправление.**
- Если `expires_in` не пришёл, `expires_at = None`. Такие соединения
  refresher не трогает.
- Если токен когда-нибудь будет с `expires_in` и refresh token, обновление
  работает как раньше, но больше не падает, когда при refresh нет `expires_in`.
- Соединение помечается `expired, reconnect` только тогда, когда сам Intervals
  отвечает 401 на запрос с этим токеном (то есть доступ действительно отозван).

## Дополнительно

- Ривер был подключён до появления календаря, поэтому у него нет
  `CALENDAR:WRITE`. Теперь `/api/intervals/status` возвращает
  `missing_scopes`, а в карточке есть кнопка «Reconnect» с объяснением.
  При подключении с неполными правами пишется запись в лог.
- Токен Ривера уже стёрт из базы (`access_token=None`), поэтому Риверу нужно
  подключиться ещё раз, теперь кнопкой. Ему в любом случае нужно выдать
  доступ к календарю.

## Проверка

Весь поток проверен локально с фейковым token endpoint: без токена init
отдаёт 401, с токеном — authorize URL с новыми scope; callback возвращает
302 на `/?connected=1`; status показывает `connected`, соединение без срока
действия, и `missing_scopes: []`. Настоящий Intervals.icu не вызывался.
