# Почему nightly-review ничего не сообщала

## Что показывают файлы

`launchctl-print.txt` (снимок 2026-10-18): `runs = 6`, `last exit code = 1`. Задание запускалось по расписанию (02:30), то есть launchd работал. Проблема не в расписании.

`Library/Logs/nightly-review.err` содержит 6 пар строк, по одной на запуск, и каждый раз две ошибки:

1. `Not logged in · Please run /login` — от `claude -p`.
2. `/Users/vk/bin/nightly-review.zsh:19: read-only variable: status` — от самого скрипта.

Число 6 совпадает с `runs = 6`: все запуски упали.

`Library/Logs/nightly-review.out` пустой, что ожидаемо: `claude` пишет ошибку в stderr, а в stdout ничего.

## Две причины, наложенные друг на друга

**Причина 1: CLI не видит логин.** В plist нет `USER`. Headless `claude` под launchd не находит свой логин в keychain и падает с `Not logged in`. Исправление: добавить `USER` в `EnvironmentVariables`.

**Причина 2: сообщатель падает раньше, чем сообщит.** В строке `status=$?` zsh переменная `status` встроенная и только для чтения. Присваивание убивает скрипт на месте, до вызова `notify.sh`. Поэтому провал агента не доходит до Telegram, и вы не получили ни одного уведомления, ни успеха, ни ошибки. Это и есть «полная тишина». Исправление: `rc=$?`.

## Третья скрытая проблема (тоже исправлена)

В `notify.sh` при недоступном keychain `TG_BOT_TOKEN` становился пустым, и запрос уходил на `https://api.telegram.org/bot/sendMessage`. Без `curl -f` ответ 404 не считался ошибкой, и скрипт выходил с 0 без следа. Теперь пустой токен даёт ошибку в stderr и exit 1, а `curl -fsS` возвращает ненулевой код на HTTP-ошибки.

## Что изменено

- `Library/LaunchAgents/com.vk.nightly-review.plist`: добавлен `USER` = `vk`.
- `bin/nightly-review.zsh`:
  - `status` → `rc`;
  - `< /dev/null` при вызове `claude`;
  - в stderr пишется время старта и длительность, чтобы видеть, что запуск реально шёл;
  - пустой вывод при коде 0 считается провалом и отправляет уведомление.
- `bin/notify.sh`: пустой токен — ошибка; `curl -fsS`.

## Проверка

В песочнице (подменены `HOME`, `claude` и `notify.sh`; настоящий Telegram не вызывался):

- Исходный скрипт воспроизвёл ошибку из `.err`: `read-only variable: status`, уведомления нет.
- Исправленный скрипт при падении `claude` (exit 1) отправляет `FAILED (exit 1)`.
- При успехе отправляет `done: <summary>`.
- При exit 0 и пустом выводе отправляет `FAILED (empty output)`.
- `plutil -lint` для plist: OK. `bash -n` и `zsh -n`: OK.

## Что не проверено и что нужно сделать на вашей машине

Я работаю со снимком, поэтому не могу перезагрузить задание. Выполните:

1. `launchctl bootout gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist`, затем `launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist`.
2. `launchctl kickstart -k gui/$UID/com.vk.nightly-review`.
3. Проверьте `launchctl print gui/$UID/com.vk.nightly-review`: `last exit code = 0`, и есть свежий файл `~/Library/Logs/nightly-review-<дата>.md` с осмысленным текстом. Длительность в `.err` должна быть реалистичной (не 0–2 секунды).
4. Убедитесь, что пришло сообщение в Telegram.
5. Проверьте обратное: временно сломайте, например, `REPO`, и убедитесь, что пришло сообщение об ошибке.

Не проверено: что `security find-generic-password -s tg-bot` работает под launchd на вашей машине. Если в шаге 4 сообщения нет, а в `.err` есть `no Telegram token`, значит keychain недоступен из launchd. Тогда нужен другой способ передать токен, и это отдельная задача.

## Какие части заметки коллеги пригодились

- **Пригодилось:** `status` — read-only в zsh, поэтому `rc=$?` (причина 2).
- **Пригодилось:** `USER` в `EnvironmentVariables` при ошибке «Not logged in» (причина 1).
- **Пригодилось:** `< /dev/null` при передаче промпта аргументом.
- **Пригодилось:** лог длительности и проверка реального результата, а не только кода выхода. Именно пустой вывод с кодом 0 стал бы незамеченным сбоем.
- **Пригодилось:** `launchctl print` как первый шаг. Он подтвердил, что задание запускалось (`runs = 6`), и показал код выхода.
- **Не понадобилось:** передача промпта через stdin. Здесь промпт уже передаётся аргументом, и ошибки парсинга аргументов нет: `claude` падает раньше, на логине.
- **Не понадобилось:** «Input must be provided either through stdin or as a prompt argument». В ваших логах этой ошибки нет.
- **Не проверено:** перезапуск через `launchctl kickstart` и проверка уведомления об успехе. Для этого нужна ваша машина, см. шаги выше.
