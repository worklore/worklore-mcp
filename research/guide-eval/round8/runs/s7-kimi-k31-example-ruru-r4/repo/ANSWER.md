# Причины сбоя интеграции Intervals.icu

## 1. Кнопка Connect не отправляла токен аутентификации tricoach

Кнопка была обычной ссылкой на `GET /api/intervals/auth/init`. При переходе по ссылке браузер не добавляет `Authorization: Bearer ...`, который SPA хранит в `localStorage` и подставляет только в `fetch`. Поэтому endpoint справедливо возвращал 401 всем пользователям (`logs/connect-attempt.log:5`, `logs/support-tickets.md:3`).

Теперь Connect вызывает аутентифицированный `POST /api/intervals/auth/init` через общий fetch-wrapper. Backend возвращает `{authorize_url}`, а SPA выполняет `window.location.assign(authorize_url)` (`static/app.js`, `server.py`).

## 2. Authorize URL содержал повторные области scope

В `config.py` одновременно запрашивались `ACTIVITY:READ,ACTIVITY:WRITE` и `CALENDAR:READ,CALENDAR:WRITE`. У Intervals.icu `:WRITE` уже включает `:READ`; повторение области приводит к отказу authorize-запроса до показа consent screen. Это объясняет HTTP 400 у вручную построенной ссылки (`logs/connect-attempt.log:15`, `logs/support-tickets.md:24`).

Scope исправлен на `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`: каждая область указана один раз, при этом сохранены чтение wellness и запись тренировок в календарь.

## 3. Бессрочный токен искусственно истекал через час

В успешном ответе не было ни `refresh_token`, ни `expires_in`, но backend подставлял собственный TTL 3600 секунд. Фоновая задача затем удаляла рабочий access token и ставила статус `expired, reconnect` (`logs/connect-attempt.log:37`, `logs/connect-attempt.log:40`). Это было локальное выдуманное истечение срока, а не отзыв со стороны Intervals.icu; отметка в поддержке подтверждает, что Rivera доступ не отзывал (`logs/support-tickets.md:20`).

У Intervals.icu access token действует до отзыва и не обновляется по refresh token. Фиктивный TTL и фоновый refresher удалены. Реальный 401 от API теперь обрабатывается лениво: сохранённый токен очищается, а статус становится `revoked, reconnect`. После этого можно подключиться повторно.

## Дополнительные исправления совместимости и безопасности

- Обмен кода в `POST /api/oauth/token` теперь отправляет только `client_id`, `client_secret` и `code`; лишние `grant_type` и `redirect_uri` удалены.
- Подписанный `state` сохраняет существующий HMAC-механизм проекта, но дополнительно содержит и проверяет `purpose=intervals_oauth`, срок 15 минут, известного пользователя и корректную метку времени.
- При повторном подключении callback отклоняет другой `athlete.id`, не перезаписывая существующее соединение.
- Ответ token endpoint проверяется на наличие `access_token` и `athlete.id`.

## Что пригодилось из заметки коллеги

Использованы все четыре основных наблюдения: бессрочный токен без refresh, правило уникальных scope, минимальный набор полей обмена кода и authenticated POST для init с JSON-ответом. Также применены рекомендации из продолжения заметки: назначение и TTL `state`, защита от смены аккаунта при повторном подключении и очистка соединения после реального 401.

Конкретный JWT для `state` не понадобился: уже существующий HMAC-подписанный state решает ту же задачу без новой зависимости, поэтому проект остаётся stdlib-only. Шифрование постоянного хранилища не добавлялось: в этом репозитории токены хранятся только в памяти, персистентного хранилища здесь нет.

## Проверка

Локальный HTTP-имитатор Intervals.icu и реальный handler приложения использованы для полного сценария: POST init, проверка authorize URL и scope, callback, точные поля token exchange, status, wellness, отклонение другого athlete, отзыв через 401 и повторное подключение. Все проверки прошли. Отдельно выполнен JavaScript-обработчик Connect: подтверждены POST, заголовок `Authorization` и переход по возвращённому `authorize_url`. Синтаксические проверки Python/JavaScript и `git diff --check` также прошли.

Реальный аккаунт Intervals.icu не использовался: внешние обращения были запрещены, а в конфигурации находятся только placeholder-учётные данные. Ничего не деплоилось и не отправлялось во внешние сервисы.
