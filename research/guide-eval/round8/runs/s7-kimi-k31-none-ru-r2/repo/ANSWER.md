# Причины сбоя интеграции Intervals.icu

1. **Кнопка Connect теряла авторизацию tricoach.** В `static/app.js` использовалась обычная ссылка на `/api/intervals/auth/init`. При переходе браузер не добавлял заголовок `Authorization: Bearer ...`, который добавляется только в `fetch`, а сервер требует этот заголовок. Поэтому все получали `401 Unauthorized`. Теперь кнопка запрашивает authorize URL через авторизованный `fetch`, после чего открывает возвращённый URL.

2. **Запрашивались неподдерживаемые права `CALENDAR:READ` и `CALENDAR:WRITE`.** После их добавления Intervals.icu отклонял authorize-запрос с `invalid_request` ещё до экрана согласия. Эти права удалены из `config.py`; для чтения активностей и записи плановых тренировок используются поддерживаемые `ACTIVITY:READ` и `ACTIVITY:WRITE`, для wellness — `WELLNESS:READ`.

3. **Не запрашивался offline-доступ.** Без `access_type=offline` Intervals.icu возвращал только access token, без refresh token. Через `expires_in` (в captured-случае примерно через час) фоновой обновитель не мог продлить доступ и переводил подключение в `expired, reconnect`. Параметр `access_type=offline` добавлен в authorize-запрос. Также обновление токена теперь использует стандартный TTL, если ответ на refresh не содержит `expires_in`, и сохраняет прежний refresh token, если новый не возвращён.
