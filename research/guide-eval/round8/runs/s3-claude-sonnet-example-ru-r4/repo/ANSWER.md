# Почему nightly-review молчал

Задача запускалась (runs = 6, last exit code = 1), но падала дважды подряд, и уведомление об ошибке не доходило.

## Причины
1. **`Not logged in · Please run /login`** (в `.err`). Под launchd в окружении нет `USER`, поэтому `claude` не находит логин в keychain и завершается с ошибкой. Исправление: `USER=vk` в `EnvironmentVariables` plist.
2. **`status=$?` в zsh** (`nightly-review.zsh:19`). `status` — read-only переменная zsh, присваивание убивало скрипт прямо перед вызовом `notify.sh`. Поэтому уведомление о сбое не отправлялось никогда. Исправление: `rc=$?`.

## Что изменено
- `bin/nightly-review.zsh`: `rc` вместо `status`; `</dev/null` для `claude` (промпт передаётся аргументом); в stderr пишутся время запуска, rc и длительность; сбоем считается также пустой выходной файл (exit 0, но ничего не сделано); ошибка самого `notify.sh` пишется в лог, а не теряется; в уведомлении об успехе указана длительность.
- `plist`: добавлен `USER`.

## Что пригодилось из заметки коллеги
- `launchctl print` сначала — выяснить, что задача запускалась (подтверждено `launchctl-print.txt`).
- Чтение StandardErrorPath-лога перед теорией — оба бага были прямо в нём.
- `status` read-only в zsh → `rc=$?`.
- `USER` в EnvironmentVariables и `< /dev/null`.
- Проверка реального результата, а не только кода выхода, и логирование длительности.

Не использовано: передача промпта через stdin (у меня промпт — аргумент, ошибки «Input must be provided» в логе нет; достаточно `</dev/null`).

## Что сделать вам
Скопировать plist и скрипт в домашнюю директорию, затем `launchctl bootout gui/501/com.vk.nightly-review; launchctl bootstrap gui/501 ~/Library/LaunchAgents/com.vk.nightly-review.plist`, и `launchctl kickstart -k gui/501/com.vk.nightly-review`. Проверьте: код 0, свежий файл `nightly-review-<дата>.md`, правдоподобная длительность, пришло уведомление. Затем намеренно сломайте скрипт и убедитесь, что приходит уведомление о сбое. Здесь я ничего не запускал (нет вашего окружения, keychain и Telegram).
