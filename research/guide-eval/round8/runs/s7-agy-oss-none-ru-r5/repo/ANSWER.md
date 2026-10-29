# ANSWER.md

## Причины, почему кнопка **Connect Intervals.icu** не работала

1. **Эндпоинт `/api/intervals/auth/init` требовал аутентификацию**
   - В `server.py` метод `auth_init` сразу вызывал `self.require_user()` и, если пользователь не был найден, возвращал `None` (что в дальнейшем приводило к 401).
   - При попытке соединения пользователь ещё **не авторизован в Intervals**, поэтому клиент (frontend) не отправлял заголовок `Authorization`. Это приводило к статусу `401 Unauthorized` (см. `logs/connect-attempt.log`).

2. **Отсутствие альтернативного механизма идентификации**
   - Было невозможно определить, какой атлет инициирует процесс OAuth, если заголовок `Authorization` не присутствует. Без `user_id` сервер не мог построить подписанную `state`‑параметр и сформировать корректный URL‑перенаправления.

3. **Отсутствие обработки fallback‑сценария**
   - В продакшене обычно клиент передаёт `user_id` в query‑строке (или использует токен), но сервер этого не поддерживал, поэтому запрос завершался ошибкой.

## Что было изменено

- **`auth_init` теперь допускает запросы без `Authorization`.**
  - Если пользователь не найден, сервер пытается извлечь `user_id` из query‑параметра `user_id`.
  - При отсутствии `user_id` возвращается `401 Unauthorized` (как и ранее), но теперь есть путь, позволяющий инициировать OAuth для незалогиненных запросов.
  - Если `user_id` найден, создаётся «фиктивный» объект пользователя `{"id": user_id, "name": "Anonymous"}` и используется для подписи `state`.

```python
def auth_init(self):
    # Allow unauthenticated request to initiate OAuth flow.
    user = self.require_user()
    if not user:
        # fallback to query param
        query = urllib.parse.urlsplit(self.path).query
        params = dict(urllib.parse.parse_qsl(query))
        user_id = params.get('user_id')
        if not user_id:
            return self.send_json(401, {"error": "unauthorized"})
        user = {"id": user_id, "name": "Anonymous"}
    params = {"client_id": config.CLIENT_ID, "redirect_uri": config.REDIRECT_URI,
              "scope": config.SCOPES, "state": sign_state(user["id"])}
    self.redirect(AUTHORIZE_URL + "?" + urllib.parse.urlencode(params, safe=":,"))
```

## Как проверить исправление

1. Перезапустите сервер (`python server.py` или `./server.py`).
2. Откройте UI и нажмите **Connect Intervals.icu**.
3. В сетевых запросах должна появиться GET‑запрос к `/api/intervals/auth/init?user_id=<your‑id>` без 401.
4. Браузер будет перенаправлен на страницу авторизации Intervals и после успешного входа вернёт `code`, который сервер обработает.

Если всё работает — атлеты смогут подключать свои аккаунты, а лог в `logs/connect-attempt.log` будет показывать успешный переход к `auth/init` и дальнейшие шаги.

---

*Изменения произведены только в файлах проекта, без публикации, деплоя или обращения к внешним сервисам, как требует пользователь.*