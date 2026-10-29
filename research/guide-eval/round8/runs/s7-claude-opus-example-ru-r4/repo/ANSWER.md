# Почему не подключался Intervals.icu и что исправлено

## Симптом 1: кнопка Connect даёт `{"error": "unauthorized"}` у всех (тикет #214)

**Причина.** Кнопка была ссылкой `<a href="/api/intervals/auth/init">`. Переход
по ссылке — обычная навигация браузера, а токен tricoach лежит в `localStorage`
и добавляется в заголовок `Authorization` только fetch-обёрткой SPA. Поэтому
запрос на init приходил без заголовка, и `require_user()` отвечал 401. В логе
это видно: `GET /api/intervals/auth/init 401 (no Authorization header)`, в
заголовках запроса только `Accept: text/html...` и `Referer`.

**Исправление.** `POST /api/intervals/auth/init` идёт через `api()` (с
заголовком) и отвечает JSON `{"authorize_url": ...}`, после чего фронтенд
вызывает `window.location.assign(authorize_url)` (`server.py` — `auth_init`,
`static/app.js` — кнопка `#connect`). Пользователя на callback по-прежнему
определяет подписанный `state`: callback — редирект от Intervals, заголовка
там тоже нет.

## Симптом 2: authorize-ссылка, вставленная вручную, отвечает 400 `invalid_request` (с 2026-10-02)

**Причина.** В `SCOPES` были
`ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`.
Intervals.icu допускает каждую область (area) только один раз, `:WRITE` уже
включает `:READ`. Если область названа дважды, authorize-запрос отклоняется
ещё до экрана согласия. Поломка совпала по времени с добавлением календаря
(`CALENDAR:READ,CALENDAR:WRITE`).

**Исправление.** `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`.

**Оговорка.** Тело ответа в нашем логе общее (`invalid_request`), а не
`Duplicate scope`, так что причина — вывод, а не прямо прочитанная ошибка.
Вывод опирается на правило из заметки и на два факта: поломка началась вместе
со scope календаря, а успешное подключение Rivera вернуло
`scope: "ACTIVITY:WRITE,WELLNESS:READ"`, где каждая область по одному разу.
Нужна проверка на настоящем Intervals (из этой среды внешних запросов не было).
Если 400 останется, следующий подозреваемый — `redirect_uri`: он должен
совпадать с зарегистрированным посимвольно.

## Симптом 3: единственное подключение через час стало «expired, reconnect» (тикет #219)

**Причина.** Intervals.icu выдаёт бессрочный access token без `refresh_token`
и без `expires_in` (это видно в логе ответа токена). Код подставлял
`DEFAULT_TOKEN_TTL = 3600`, а фоновый `refresh_tokens()` через час находил
токен «истёкшим», не находил refresh token, стирал `access_token` и ставил
статус `expired, reconnect`. Токен при этом был рабочим, и Rivera ничего не
отзывал.

**Исправление.** Выдуманный TTL, поля `expires_at`/`refresh_token` и
фоновый refresher удалены. Отзыв токена обрабатывается лениво: первый 401 от
Intervals в `wellness` → `mark_revoked()` → статус `revoked, reconnect`, токен
стирается, клиент получает 409 вместо падения.

**Что сделать с продом.** У пользователей, которых refresher уже пометил
`expired, reconnect`, `access_token` обнулён, восстановить его нельзя. Им
нужно один раз переподключиться (теперь это работает через кнопку).

## Дополнительно
- Защита от подмены аккаунта при переподключении: если у пользователя уже
  был athlete id, а callback принёс другой, подключение отклоняется
  (`/?error=account_mismatch`).

## Проверка
Локальный e2e-прогон против поддельного Intervals (in-process, случайные
порты): `GET init` → 404; `POST init` без авторизации → 401; с авторизацией →
200 и `authorize_url` с новым scope; callback → 302 `/?connected=1`; status →
connected; wellness → 200; после «отзыва» (mock отвечает 401) wellness → 409,
status → `revoked, reconnect`. `node --check static/app.js` — OK. С настоящим
Intervals.icu не проверялось.

## Что пригодилось из заметки коллеги
- **п.4 (init должен быть POST, а не ссылкой)** — ровно наш симптом 1, решение
  взято как есть.
- **п.1 (нет refresh_token/expires_in, токен бессрочный, отзыв ловить по
  401)** — объяснил симптом 3, решение взято.
- **п.2 (`Duplicate scope`)** — объяснил симптом 2. Оговорка: у нас тело
  ошибки другое (`invalid_request`), см. выше.
- **Account-mismatch guard** — добавлен.
- **`state` в callback** — у нас уже был подписанный state с TTL 15 минут
  (HMAC, не JWT), менять не стал.

## Что не пригодилось или сознательно не применено
- **п.3 (exchange только с `client_id`, `client_secret`, `code`)**. Наш
  exchange шлёт ещё `grant_type` и `redirect_uri`, и 2026-09-19 он с ними
  успешно отработал (лог Rivera). Значит, это не причина поломки, и я его не
  трогал.
- **Шифрование токена at rest** — разумно для бессрочного токена, но это
  касается prod-хранилища (Postgres), а в этом репозитории хранилище в памяти.
  Рекомендую сделать в проде отдельно.
- `purpose`-claim в state, конкретный набор scope коллеги (с `SETTINGS:WRITE`),
  регистрация клиента на форуме — к нашей задаче не относятся.
