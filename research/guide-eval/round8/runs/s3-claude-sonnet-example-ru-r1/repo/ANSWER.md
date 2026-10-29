# Почему nightly-review молчал

Задача запускалась (runs = 6, last exit code = 1), логи существовали. Два слоя ошибок:

1. **`claude -p` падал с «Not logged in · Please run /login»** (см. `nightly-review.err`).
   Под launchd нет `USER` в окружении, CLI не находит логин в keychain.
   Исправление: `USER=vk` в `EnvironmentVariables` plist.
2. **`status=$?` в zsh** — `status` read-only, скрипт умирал на строке 19
   (`read-only variable: status`) ещё до вызова `notify.sh`. Уведомление об ошибке
   было *после* места падения, поэтому не пришло ничего.
   Исправление: `rc=...`.

Прочее в скрипте: `notify` обёрнут, чтобы сбой уведомления не маскировал результат;
добавлены длительность запуска в stderr-лог и проверка непустого выхода
(exit 0 при пустом результате теперь тоже даёт FAILED); промпт передаётся через
stdin (`print -r -- "$PROMPT" | claude -p`), код возврата берётся из `pipestatus[2]`.

## Что пригодилось из заметки коллеги
- `launchctl print` как первый шаг (runs / last exit code) — подтвердил, что задача запускалась.
- Чтение stderr-лога до теорий — там были обе причины.
- Не присваивать `status` в zsh — основная причина тишины.
- `USER` в plist — вторая причина (Not logged in).
- Промпт через stdin (альтернатива `< /dev/null`).
- Логирование длительности, проверка реального результата, а не только кода выхода.

Не пригодилось: «prompt not received» как причина (у вас ошибка другая — Not logged in);
история про 16:50 и watchdog; ссылки на внешние статьи не открывал.

## Что сделать вам
Я ничего не перезагружал. Примените plist и проверьте:
```
launchctl bootout gui/$UID/com.vk.nightly-review
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist
launchctl kickstart -k gui/$UID/com.vk.nightly-review
launchctl print gui/$UID/com.vk.nightly-review   # last exit code = 0
```
Проверьте свежий `nightly-review-<дата>.md`, правдоподобную длительность в `.err` и
сообщение в Telegram. Затем сломайте скрипт нарочно (например, неверный REPO или
команду) и убедитесь, что приходит FAILED. Также проверьте, что `notify.sh` под launchd
достаёт токен из keychain (`security find-generic-password` может требовать доступа
без GUI) — иначе сообщение не уйдёт, но теперь это будет видно в `.err`.
Правки в `~/bin` и `~/Library/LaunchAgents` нужно скопировать из этого снимка.
