# Причины проблем с интеграцией Intervals.icu и внесенные исправления

## 1. Причины проблем

На основе анализа логов (`logs/connect-attempt.log`, `logs/support-tickets.md`) и кодовой базы были выявлены три ключевые проблемы:

1. **Кнопка "Connect Intervals.icu" не работала ни у кого (ошибка 401 Unauthorized)**:
   - В `static/app.js` кнопка была реализована как обычная ссылка `<a href="/api/intervals/auth/init">`.
   - При обычном переходе по ссылке (полной навигации браузера) заголовок `Authorization: Bearer <token>`, хранящийся в `localStorage` SPA, не передается.
   - Эндпоинт `/api/intervals/auth/init` требовал авторизации (`require_user()`) и возвращал `401 Unauthorized` (`{"error": "unauthorized"}`).

2. **Ошибка `invalid_request` / `Duplicate scope` со стороны Intervals.icu при авторизации**:
   - В [config.py](file:///tmp/h-Na2gch/config.py) значение `SCOPES` было задано как:
     `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`
   - В Intervals.icu права `:WRITE` неявно включают `:READ`. Повторное указание одной и той же области (например, `ACTIVITY:READ,ACTIVITY:WRITE`) вызывает ошибку дублирования скоупов (`Duplicate scope` / `invalid_request`), из-за чего экран согласия даже не открывался.

3. **Единственное успешное подключение (Т. Ривера) через час перешло в статус `expired, reconnect`**:
   - Intervals.icu выдает бессрочные токены доступа без `refresh_token` и `expires_in`.
   - В [server.py](file:///tmp/h-Na2gch/server.py) было заложено предположение `DEFAULT_TOKEN_TTL = 3600`, если провайдер не вернул срок жизни токена.
   - Фоновый поток `refresh_tokens()`, проснувшись через ~3600 секунд, обнаруживал, что срок токена истек, а `refresh_token` отсутствует, и принудительно сбрасывал статус подключения в `"expired, reconnect"`.
   - Кроме того, при обмене кода на токен (`exchange_code`) отправлялись избыточные поля `grant_type` и `redirect_uri`, хотя API Intervals.icu ожидает только `client_id`, `client_secret` и `code`.

---

## 2. Внесенные изменения

1. **Инициализация OAuth через POST**:
   - В [server.py](file:///tmp/h-Na2gch/server.py) эндпоинт `/api/intervals/auth/init` переведен из метода `GET` в `POST` и возвращает JSON `{ "authorize_url": ... }`.
   - В [static/app.js](file:///tmp/h-Na2gch/static/app.js) ссылка заменена на кнопку `<button id="connect">`, которая отправляет аутентифицированный POST-запрос через SPA-обертку `api()` с передачей `Authorization` заголовка, после чего перенаправляет пользователя через `window.location.assign(res.authorize_url)`.

2. **Исправление скоупов (устранение Duplicate scope)**:
   - В [config.py](file:///tmp/h-Na2gch/config.py) строка `SCOPES` изменена на `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE` (каждая область указана не более одного раза; `:WRITE` используется там, где требуется запись).

3. **Удаление ошибочного механизма истечения и обновления токенов**:
   - В [server.py](file:///tmp/h-Na2gch/server.py) отключен фоновый поток обновления `refresh_tokens()`.
   - Из `store_connection` удалена искусственная установка срока жизни токена (токен считается бессрочным).
   - Обработка недействительности токена реализована лениво: при получении `401 Unauthorized` от API Intervals.icu (в методе `wellness`) статус подключения переводится в `"expired, reconnect"`, а токен сбрасывается.
   - В `exchange_code` запрос упрощен: передаются только `client_id`, `client_secret` и `code`.

---

## 3. Какие части заметки коллеги пригодились

Из заметки коллеги пригодились следующие пункты:

- **Пункт 1 (The token never expires and never refreshes)**:
  Полностью подтвердил причину сброса подключения Т. Риверы через час. Мы убрали искусственный TTL в 3600 секунд и фоновый рефрешер, а также добавили инвалидацию токена (`expired, reconnect`) при 401-й ошибке от API.
- **Пункт 2 ("Duplicate scope")**:
  Объяснил ошибку при переходе по вручную сгенерированной ссылке. Помог правильно сформировать список скоупов без дублирования (`ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`).
- **Пункт 3 (The token exchange is standard-lite)**:
  Помог очистить `exchange_code` от параметров `grant_type` и `redirect_uri`, оставив только `client_id`, `client_secret` и `code`.
- **Пункт 4 (Init endpoint must be POST)**:
  Объяснил причину белого экрана с `401 Unauthorized` при клике на кнопку и подсказал решение: выполнять аутентифицированный `POST /api/intervals/auth/init` из фронтенда и делать редирект через `window.location.assign`.

### Что не понадобилось / было пропущено:
- **Переделка формата `state` на JWT**: в текущем коде уже была реализована работающая схема подписи `state` с HMAC-SHA256 (`sign_state` / `verify_state` с TTL 15 минут), поэтому заменять её на JWT не потребовалось.
- **Шифрование токенов в БД (encrypt at rest)**: приложение пока работает с in-memory хранилищем данных для локальной разработки.
- **Проверка несовпадения athlete id (account-mismatch guard)**: для базового восстановления работоспособности интеграции не потребовалась.
