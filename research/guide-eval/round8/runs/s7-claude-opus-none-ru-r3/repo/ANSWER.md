# Почему не подключался Intervals.icu и что исправлено

Тут три независимые причины. Каждая сама по себе ломает подключение.

## 1. Кнопка Connect всегда отдаёт 401 (тикет #214)

Сессия в tricoach держится только на заголовке `Authorization: Bearer <token>`.
Токен лежит в `localStorage`, и этот заголовок подставляет fetch-обёртка `api()`.
А кнопка «Connect Intervals.icu» была обычной ссылкой
`<a href="/api/intervals/auth/init">`. При переходе по ссылке браузер не
передаёт никаких `Authorization`-заголовков (куки здесь тоже нет), поэтому
`require_user()` отвечал `401 {"error": "unauthorized"}`. В логе так и видно:
`401 (no Authorization header)`, а в запросе только `Accept` и `Referer`.
Ошибка была у всех без исключения. Rivera подключился лишь потому, что ссылку
на authorize ему вставили вручную.

**Исправление.** `/api/intervals/auth/init` теперь возвращает JSON
`{"url": "<authorize URL>"}`, а не 302. SPA запрашивает его через `api()`, то
есть с Bearer-токеном, и затем делает `location.href = url`. Просто отдать 302 на
fetch-запрос нельзя: fetch сам пошёл бы по кросс-доменному редиректу на
intervals.icu, и браузер его не открыл бы.

## 2. Intervals отвечает на authorize `400 invalid_request` (лог, п. 2)

С 2026-10-02 вместе с синхронизацией календаря в `config.SCOPES` указано
`ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`.
В Intervals.icu на каждую область (ACTIVITY, WELLNESS, CALENDAR, …) даётся одно
значение, `:READ` или `:WRITE`, и `WRITE` уже включает чтение. Если указать
одну область дважды, запрос получается некорректным. Это совпадает с
наблюдениями: убираешь `state` или меняешь `redirect_uri`, ответ тот же; а
сентябрьский запрос с `ACTIVITY:WRITE,WELLNESS:READ` (см. scope в
token-ответе у Rivera) проходил.

**Исправление.** `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`.

## 3. «Expired, reconnect» через час после подключения (тикет #219)

Access-токены Intervals.icu не истекают: они действуют, пока атлет не отзовёт
доступ к приложению. Поэтому в token-ответе нет ни `expires_in`, ни
`refresh_token` (у Rivera именно так). Код же при отсутствии `expires_in`
подставлял `DEFAULT_TOKEN_TTL = 3600`. Через час фоновый refresher видел, что
«срок вышел», а refresh-токена нет, и стирал `access_token` со статусом
`expired, reconnect`, хотя на стороне Intervals токен был рабочим, а приложение
не отозвано.

**Исправление.**
- Нет `expires_in` → `expires_at = None`, срока нет. Refresher такие
  подключения не трогает. Если провайдер срок всё-таки прислал, токен
  обновляется по `refresh_token`, а когда его нет, соединение помечается
  истёкшим только после реального окончания срока, а не за 5 минут до него.
  Ответ на refresh без `expires_in` больше не падает с `KeyError`.
- Refresher больше не держит глобальный `LOCK` во время сетевых запросов к
  Intervals.
- Соединение помечается `expired, reconnect` по реальному сигналу: Intervals
  ответил 401 на запрос с токеном (доступ отозван).

## Сопутствующие мелочи

- Атлет мог выдать не все запрошенные права. Например, у Rivera токен без
  `CALENDAR`, его выдали ещё до синхронизации календаря. Теперь `/status`
  отдаёт `missing_scopes`, а UI показывает «Missing access …» с кнопкой
  Reconnect.
- Если Intervals вернул на callback `?error=...` (атлет отказал на экране
  согласия), пользователь попадает назад в приложение с понятным сообщением,
  а не на `{"error": "bad state or code"}`.

## Что нужно сделать людям

- Rivera (и всем, кто успел получить `expired, reconnect`) нужно один раз
  подключиться заново через кнопку: прежний токен приложение уже стёрло. Но и
  без этого его старому токену не хватает `CALENDAR:WRITE`.

## Проверка

Прогнал локально против mock-сервера Intervals на отдельном порту:
- без токена `auth/init` отдаёт 401;
- с токеном возвращается URL со scope `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`;
- callback отдаёт 302 на `/?connected=1`, а `status` возвращает `connected`,
  `no expiry` и `missing_scopes: []`;
- `?error=access_denied` редиректит на `/?intervals_error=access_denied`.

С настоящим intervals.icu не проверял, внешних запросов не было.
