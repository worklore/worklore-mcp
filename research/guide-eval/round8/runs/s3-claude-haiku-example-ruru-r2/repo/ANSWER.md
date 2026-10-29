# Почему nightly-review ничего не сообщала

## Что показали файлы

- `launchctl-print.txt` (снимок от 2026-10-18): `runs = 6`, `last exit code = 1`. Задача запускалась, и каждый раз падала. Это не «launchd не запускает».
- `Library/Logs/nightly-review.err`: шесть пар строк. Каждая пара — `Not logged in · Please run /login`, затем `/Users/vk/bin/nightly-review.zsh:19: read-only variable: status`. Число пар совпадает с `runs = 6`.
- `Library/Logs/nightly-review.out` пустой. Это нормально: вывод `claude` идёт не в stdout, а в файл `nightly-review-ДАТА.md`, и скрипт не пишет в stdout ничего, кроме того, что уходит через `notify.sh`.

## Причина 1: задача падала, потому что claude не видел логина

`claude -p` выходит с кодом 1 с сообщением `Not logged in`. В launchd-окружении, судя по `environment` в `launchctl print`, нет переменной `USER`. Claude Code ищет OAuth-токен в keychain по имени пользователя из `USER`, поэтому не находит его. Это гипотеза, а не подтверждённый факт: в песочнице нет вашего keychain и нет запуска под launchd. Подтвердить можно только запуском на вашей машине (см. «Что сделать»). Исправление: `USER` в `EnvironmentVariables` plist-файла.

## Причина 2: ошибка не сообщалась, потому что скрипт падал раньше уведомления

В zsh `status` — read-only переменная. Строка `status=$?` в `bin/nightly-review.zsh:19` убивала скрипт сразу после вызова claude. Ветка `if [ $status -ne 0 ]` с `notify.sh` не выполнялась никогда. Воспроизведено локально: исходный скрипт с фейковым claude, который выходит с 0, даёт `read-only variable: status`, и уведомления нет.

Это и есть «тишина в два слоя»: задача падала (причина 1), а репортёр ошибок умирал до того, как мог что-то сказать (причина 2).

## Причина 3 (найдена при разборе): notify.sh тоже мог молчать

`: "${TG_BOT_TOKEN:=$(security find-generic-password -s tg-bot -w)}"` при `set -e` не падает, если `security` не нашёл токен. Дальше `curl -sS` без `-f` на HTTP 404 возвращает код 0 и прячет ответ в `/dev/null`. Воспроизведено: исходный `notify.sh` с пустым токеном завершается с кодом 0 и ничего не делает. Даже после исправления причины 2 уведомления могли бы не приходить.

## Что изменено

1. `bin/nightly-review.zsh`
   - `status=$?` → `rc=$?`, плюс комментарий, почему не `status`.
   - Промпт передаётся через stdin: `print -r -- "$PROMPT" | claude -p --output-format text`.
   - Логируются старт и `claude exit=... duration=...s` (в stdout, то есть в `nightly-review.out`).
   - Пустой вывод при коде 0 считается ошибкой и отправляется уведомлением.
2. `bin/notify.sh`
   - Явная проверка токена: если в keychain его нет, выводится понятная ошибка и скрипт завершается с кодом 1.
   - `curl -fsS`: HTTP-ошибка Telegram делает скрипт неуспешным и печатает причину в stderr.
3. `Library/LaunchAgents/com.vk.nightly-review.plist`
   - Добавлен `USER` = `vk`. Значение взято из путей `/Users/vk/...` в снимке. Проверьте `id -un`.

## Что проверено, а что нет

Проверено локально, с фейковыми `claude`, `curl` и `security` (всё удалено после прогона):
- исходный скрипт: падает на `status`, уведомления нет;
- исправленный скрипт: успех → уведомление «done»; `claude` с кодом 1 → уведомление «FAILED (exit 1 after 0s)»; код 0 с пустым выводом → уведомление об ошибке;
- `notify.sh`: без токена даёт ошибку и код 1; при HTTP 404 даёт код 22 (раньше давал 0);
- `zsh -n`, `bash -n`, `plutil -lint` проходят.

Не проверено (нужна ваша машина):
- что `USER` действительно устраняет `Not logged in` под launchd;
- что `print ... | claude -p` работает с настоящим CLI (в песочнице я не запускал настоящий claude, чтобы не тратить аккаунт);
- что `security find-generic-password` работает из launchd-сессии;
- сам plist под `launchctl bootout/bootstrap` и `kickstart`.

Снимок `launchctl print` от 2026-10-18. Что происходило после, из файлов неизвестно. Смотрите текущие `.err` и `launchctl print` на машине.

## Что из заметки коллеги пригодилось

- **Пригодилось:** `rc=$?` вместо `status`; промпт через stdin; логирование длительности; пустой вывод при коде 0 считать провалом; `USER` в `EnvironmentVariables`; проверка уведомления об ошибке, намеренно вызванной.
- **Пригодилось, но по-другому:** в заметке первый слой — «промпт не доходит до claude» (`Input must be provided...`). У вас его не было, первый слой — `Not logged in`. Поэтому исправление промпта не было главным, а `USER` стал основным.
- **Не пригодилось:** `< /dev/null` при передаче промпта аргументом. Промпт теперь идёт через stdin, поэтому это не нужно. Это разумная страховка, если вернётесь к аргументу.
- **Не пригодилось:** `launchctl print` как доказательство «не врёт». В вашем случае код 1 честный, но в общем случае заметка сама это поправляет, и я опирался на правку: проверяйте реальный результат (файл и уведомление), а не только код выхода.
- **Не использовано:** ссылку на статью Михая Пердума я не открывал. Опирался только на изложенные в заметке пункты.

## Что сделать на вашей машине

Я ничего не копировал в домашнюю директорию и не перезагружал launchd.

```sh
id -un    # должно быть vk; если нет, поправьте USER в plist
cp bin/nightly-review.zsh bin/notify.sh ~/bin/
cp Library/LaunchAgents/com.vk.nightly-review.plist ~/Library/LaunchAgents/
launchctl bootout gui/$UID/com.vk.nightly-review
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist
launchctl kickstart -k gui/$UID/com.vk.nightly-review
```

Проверка успеха, всё вместе:
- `launchctl print gui/$UID/com.vk.nightly-review | grep -E 'runs|last exit'` → `last exit code = 0`;
- `~/Library/Logs/nightly-review-$(date +%F).md` существует, не пустой и свежий;
- `~/Library/Logs/nightly-review.out` показывает длительность в секундах, и это не 0–2 секунды;
- `~/Library/Logs/nightly-review.err` пустой;
- пришло сообщение «done» в Telegram.

Проверка ошибки: `mv ~/projects/shop ~/projects/shop.off`, затем `kickstart -k`. Ожидается «repo missing» в Telegram. После проверки верните каталог назад.

Если после `USER` всё ещё `Not logged in`, логин лежит в keychain, и причина не в переменных. Тогда нужен `claude` в интерактивном терминале, чтобы выполнить вход заново. Это уже вне того, что можно проверить здесь.
