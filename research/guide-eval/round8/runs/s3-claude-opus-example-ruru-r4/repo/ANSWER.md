# Почему nightly-review ни разу ничего не сообщил

## Что показали факты (до всяких теорий)

- `launchctl-print.txt`: `runs = 6`, `last exit code = 1`, `state = waiting`.
  Агент загружен 2026-10-12, снимок от 2026-10-18 09:10 — это ровно 6 ночей
  (13–18 октября) в 02:30. **launchd работает и запускает задачу каждую ночь**,
  проблема внутри скрипта.
- `Library/Logs/nightly-review.err` — 6 одинаковых пар строк:
  ```
  Not logged in · Please run /login
  /Users/vk/bin/nightly-review.zsh:19: read-only variable: status
  ```
- `nightly-review.out` пуст: до `notify.sh` дело не доходило ни разу (иначе
  ошибки curl/`security` из `set -eu` в notify.sh были бы видны в логе).

## Причина 1 — `claude -p` падает с «Not logged in»

В `EnvironmentVariables` plist задан только `PATH`. Без `USER` в окружении
launchd CLI не находит свой логин в keychain и сразу выходит с ошибкой
(руками из терминала всё работает, потому что там `USER` есть). Это сама
ошибка задачи.

**Исправление:** в plist добавлены `USER=vk` (и на всякий случай `HOME=/Users/vk`).

## Причина 2 — `status=$?` убивает скрипт до уведомления об ошибке

В zsh `status` — встроенная read-only переменная (синоним `$?`). Строка 19
`status=$?` завершает скрипт с кодом 1 («read-only variable: status»). Она
стоит ровно между вызовом `claude` и веткой `if [ $status -ne 0 ]; then notify ...`,
поэтому сообщение о провале не отправлялось никогда. Отсюда полная тишина:
задача падает, а «гонец» умирает раньше, чем успевает что-то сказать.
(`last exit code = 1` — это как раз код этой ошибки zsh.)

**Исправление:** `rc=$?` вместо `status=$?`.

## Что ещё изменено в `bin/nightly-review.zsh` (чтобы тишина стала невозможной)

- Промпт передаётся через stdin (`print -r -- "$PROMPT" | claude -p ...`), а
  не многострочным аргументом — заодно у `claude` не остаётся открытого stdin,
  которого он мог бы ждать.
- `trap ... EXIT`: если скрипт умирает по любой непредусмотренной причине до
  явного уведомления, всё равно уходит сообщение «died unexpectedly (exit N)».
- Успех теперь = код 0 **и** непустой результат; пустой вывод при коде 0
  считается провалом.
- stderr `claude` пишется в `nightly-review-ДАТА.err`, хвост попадает в
  сообщение о провале (видно «Not logged in» прямо в Telegram).
- В лог пишутся время старта, `USER`, код выхода и длительность запуска
  (запуск в пару секунд = упал до начала работы).
- Если сам `notify.sh` упал, это фиксируется в логе, а не исчезает молча.

Проверено локально с поддельными `claude` и `notify.sh` (ничего наружу не
отправлялось): успех → «done»; «Not logged in» → «FAILED … Not logged in»;
код 0 с пустым выводом → «FAILED»; вернул старый баг `status=$?` → пришло
«died unexpectedly (exit 1)»; упавший notify → запись в логе. `plutil -lint`
для plist — OK.

## Что сделать у себя (я ничего не запускал в launchd)

```sh
launchctl bootout gui/$UID/com.vk.nightly-review
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist
launchctl kickstart -k gui/$UID/com.vk.nightly-review
launchctl print gui/$UID/com.vk.nightly-review | grep -E 'runs|last exit'
tail ~/Library/Logs/nightly-review.err   # длительность должна быть не секунды
```
Убедиться, что пришло сообщение в Telegram и появился свежий
`~/Library/Logs/nightly-review-ДАТА.md`. Затем один раз сломать задачу
намеренно (например, временно `REPO=/nonexistent`) и убедиться, что пришло
сообщение о провале. Остаточный риск: `notify.sh` берёт токен через
`security find-generic-password`; если в 02:30 login keychain заблокирован,
уведомление не уйдёт — но теперь это будет видно в логе.

## Какие части заметки коллеги пригодились

- **Пригодилось:** «сначала докажите, запускалась ли задача» через
  `launchctl print` (runs/last exit code) и «читайте лог из StandardErrorPath
  до теорий» — это сразу дало обе причины. Баг `status=$?` в zsh — один в один
  наша причина 2. Совет про `USER` в `EnvironmentVariables` против «Not logged
  in» (из ссылки на Пердума) — наша причина 1. Передача промпта через stdin,
  логирование длительности, проверка реального результата, а не только кода
  выхода, и намеренная проверка пути ошибки — применены.
- **Не пригодилось / не наш случай:** ошибка «Input must be provided either
  through stdin or as a prompt argument» в логе не встречалась (промпт через
  stdin я сделал как профилактику, не как исправление); `< /dev/null` не нужен,
  раз промпт идёт через stdin; сторожевой таймер с выходом 0 — у нас его нет.
  Поправка про то, что код выхода не доказывает успех, учтена проверкой
  непустого вывода.
