# Причины проблем с интеграцией Intervals.icu и описание исправлений

## 1. Выявленные причины проблем

1. **Кнопка «Connect Intervals.icu» отдавала 401 Unauthorized всем пользователям**
   - **Причина**: Кнопка в `static/app.js` была оформлена как обычная ссылка `<a class="btn" href="/api/intervals/auth/init">`. При прямом переходе по ссылке браузер выполняет полную навигацию документа (GET-запрос) без заголовка `Authorization: Bearer <token>`, который хранится в `localStorage` SPA. Эндпоинт `/api/intervals/auth/init` требовал авторизованного пользователя (`require_user()`) и закономерно возвращал `401 Unauthorized` (`{"error": "unauthorized"}`).
   - **Вторая проблема на шаге авторизации (Duplicate scope / 400 Bad Request)**: При попытке сформировать ссылку вручную Intervals.icu возвращал ошибку `400 invalid_request` (Duplicate scope), так как в `config.py` строка скоупов содержала:
     `"ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE"`.
     В модели прав Intervals.icu `:WRITE` уже включает в себя права `:READ`. Указание одновременно и `:READ`, и `:WRITE` для одной области расценивается Intervals.icu как дублирование скоупа и отклоняется.

2. **Потеря подключения у T. Rivera через 1 час («expired, reconnect»)**
   - **Причина**: OAuth-токены Intervals.icu не имеют срока действия (`expires_in`) и не предоставляют `refresh_token` — токен действителен до тех пор, пока атлет сам не отзовет доступ в настройках Intervals.icu.
   - В `server.py` в функции `store_connection` при отсутствии `expires_in` устанавливался таймер по умолчанию `DEFAULT_TOKEN_TTL = 3600` (1 час). Фоновый поток `refresh_tokens` раз в минуту проверял токены с истекающим сроком, не находил `refresh_token` и по истечении часа принудительно переводил статус подключения в `"expired, reconnect"`, стирая `access_token`.

3. **Лишние параметры в обмене кода на токен (`POST /api/oauth/token`)**
   - Функция `exchange_code` отправляла параметры `grant_type="authorization_code"` и `redirect_uri`. Согласно специфике эндпоинта обмена токенов Intervals.icu (`POST /api/oauth/token`), требуются только поля `client_id`, `client_secret` и `code`.

---

## 2. Какие части заметки коллеги пригодились

Из заметки коллеги пригодились следующие пункты:
- **Пункт 1 (Токен не истекает и нет refresh_token, ленивая обработка отзыва токена)**: Пригодился полностью. Убрано искусственное ограничение времени жизни токена (TTL 1 час) и фоновая инвалидация при отсутствии `refresh_token`. Добавлена ленивая обработка отзыва: при получении `401 Unauthorized` от API Intervals.icu (например, в `/api/intervals/wellness`) статус подключения переводится в `"expired, reconnect"` и токен сбрасывается.
- **Пункт 2 ("Duplicate scope")**: Пригодился полностью. Исправлен `SCOPES` в `config.py`: удалены дублирующие `:READ` там, где есть `:WRITE`, оставлена строка `"ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`.
- **Пункт 3 (Обмен кода на токен без лишних параметров)**: Пригодился полностью. В `exchange_code` (`server.py`) убраны `grant_type` и `redirect_uri`, оставлены только `client_id`, `client_secret`, `code`. Также используется `athlete: {id, name}` из ответа токена.
- **Пункт 4 (Init-эндпоинт как POST, возвращающий JSON с `authorize_url`)**: Пригодился полностью. Init-эндпоинт переведен на `POST /api/intervals/auth/init`, возвращающий `{"authorize_url": ...}`. Во фронтенде (`static/app.js`) ссылка заменена на кнопку `<button>`, которая вызывает `api("/api/intervals/auth/init", { method: "POST" })` с заголовком авторизации пользователя из `localStorage`, а затем перенаправляет пользователя через `window.location.assign(res.authorize_url)`.
- **Защита от несовпадения аккаунтов (из описания callback)**: В `store_connection` добавлена проверка, отклоняющая повторное подключение, если полученный `athlete.id` отличается от уже привязанного для данного пользователя.

Что не потребовалось менять:
- Механизм подписанного `state` в целом уже был реализован в `server.py` (`sign_state` и `verify_state`), переписывать его на стороннюю библиотеку JWT не потребовалось, так как проект использует только стандартную библиотеку Python.
