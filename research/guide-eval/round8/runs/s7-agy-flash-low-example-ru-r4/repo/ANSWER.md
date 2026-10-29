# Причины неполадок интеграции с Intervals.icu и внесенные исправления

## 1. Причины неполадок

### Почему кнопка «Connect» не работала ни у кого (Support Ticket #214)
- **Причина:** Эндпоинт инициализации OAuth `/api/intervals/auth/init` был реализован как HTTP `GET`, а кнопка в SPA была обычной ссылкой `<a href="/api/intervals/auth/init">`. При стандартном клике/навигации браузера заголовки не передаются, соответственно токен авторизации tricoach (`Authorization: Bearer ...`, хранящийся в `localStorage`) на сервер не отправлялся. Сервер возвращал `401 Unauthorized` (`{"error": "unauthorized"}`).
- Дополнительно: после добавления синхронизации календаря в скоупах запроса авторизации возникла ошибка `Duplicate scope` (`HTTP 400 invalid_request` от Intervals.icu), из-за чего даже прямой переход по сформированной ссылке авторизации завершался ошибкой: скоупы `ACTIVITY:READ,ACTIVITY:WRITE` и `CALENDAR:READ,CALENDAR:WRITE` дублировали права, так как `:WRITE` в API Intervals.icu уже включает в себя `:READ`.

### Почему единственного пользователя попросили подключиться заново через час (Support Ticket #219)
- **Причина:** Токены доступа Intervals.icu OAuth являются бессрочными (perpetual) и не имеют срока истечения (`expires_in`) или refresh-токена (`refresh_token`). 
- В приложении же при отсутствии `expires_in` токену по умолчанию выставлялся срок жизни в 1 час (`DEFAULT_TOKEN_TTL = 3600`), после чего фоновый процесс `refresh_tokens()`, не обнаружив `refresh_token`, принудительно переводил статус подключения в `"expired, reconnect"` и обнулял токен.

---

## 2. Какие части из заметки коллеги пригодились

Из заметки коллеги пригодились следующие ключевые моменты:

1. **Раздел 1 («The token never expires and never refreshes»):**
   - Убрали искусственное истечение токена через 3600 с и фоновый рефреш. Токены Intervals живут постоянно, пока пользователь не отзовет доступ.
   - Реализовали ленивую обработку отзыва (lazy revocation): при получении `401 Unauthorized` от API Intervals.icu сохраненный токен сбрасывается, а статус переводится в `reconnect`.

2. **Раздел 2 («"Duplicate scope"»):**
   - Исправили список скоупов в `config.py`. Поскольку `:WRITE` неявно включает `:READ`, убрали дубликаты областей: вместо `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE` установили `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.

3. **Раздел 3 («The token exchange is standard-lite»):**
   - В вызове `POST /api/oauth/token` (`exchange_code`) убрали лишние параметры `grant_type` и `redirect_uri`, оставив только обязательные для Intervals.icu поля: `client_id`, `client_secret` и `code`.
   - Использовали данные атлета (`athlete.id`), приходящие прямо в ответе на обмен кода.

4. **Раздел 4 («Init endpoint must be POST» и защита от подмены аккаунта):**
   - Перевели `/api/intervals/auth/init` на метод `POST` с аутентификацией через SPA fetch-клиент (передающий заголовок `Authorization: Bearer`). Сервер возвращает JSON `{authorize_url: ...}`, а фронтенд выполняет `window.location.assign(res.authorize_url)`.
   - Добавили guard-проверку (account-mismatch guard) при реконнекте: если к аккаунту пользователя уже был привязан определенный Intervals `athlete_id`, подключение другого `athlete_id` блокируется.

### Что было пропущено / не потребовалось менять:
- Механизм `state`: в приложении уже использовалась корректная подпись `state` через HMAC/timestamp, менять логику генерации и валидации `state` не потребовалось.
- Шифрование токенов в постоянном хранилище (DB at rest): в данном тестовом сервисе БД отсутствует (данные хранятся in-memory).

---

## 3. Внесенные изменения в кодовой базе

1. **`config.py`**:
   - Обновлен `SCOPES`: `"ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`.
2. **`static/app.js`**:
   - Кнопка «Connect Intervals.icu» переведена со ссылки `<a>` на `<button>`, обработчик клика отправляет авторизованный `POST /api/intervals/auth/init` и выполняет редирект через `window.location.assign`.
3. **`server.py`**:
   - Обработка `/api/intervals/auth/init` перенесена из `do_GET` в `do_POST` и возвращает `{"authorize_url": ...}`.
   - `exchange_code`: отправляются только `client_id`, `client_secret`, `code`.
   - `store_connection`: удалено выставление искусственного TTL; добавлена проверка несовпадения `athlete_id` при переподключении.
   - `refresh_tokens`: деактивирован фоновый сброс токенов при отсутствии `refresh_token`.
   - `intervals_get`: при `401 Unauthorized` от API токен сбрасывается, и статус пользователя устанавливается в `reconnect`.
