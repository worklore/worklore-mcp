# Почему nightly-review молчал

## Что показали данные

- `launchctl-print.txt`: `runs = 6`, `last exit code = 1`. Задача **запускалась** каждую ночь
  (12.10 загружена → 13–18.10 = 6 запусков) и каждый раз падала. Проблема не в расписании launchd.
- `Library/Logs/nightly-review.err` — одна и та же пара строк на каждый запуск:
  ```
  Not logged in · Please run /login
  /Users/vk/bin/nightly-review.zsh:19: read-only variable: status
  ```

## Причины (две, одна поверх другой)

1. **`claude -p` падает с «Not logged in».** launchd не задаёт переменную `USER`
   (в `environment` из `launchctl print` есть только `PATH` и `XPC_SERVICE_NAME`), и без неё CLI
   не находит свой логин в связке ключей. Вручную из терминала `USER` есть, поэтому там всё работает.
2. **Уведомление о сбое не успевало отправиться.** Строка 19, `status=$?`: в zsh `status` —
   встроенная переменная только для чтения. В неинтерактивном скрипте присваивание ей —
   фатальная ошибка, и zsh сразу завершается с кодом 1 (проверил: `zsh -c 'false; status=$?; echo reached'`
   ничего не выводит, exit=1). Эта строка стоит между вызовом `claude` и `notify.sh`, поэтому
   до вызова уведомления дело не доходило ни при ошибке, ни при успехе. Отсюда полная тишина.

## Что исправлено

- `Library/LaunchAgents/com.vk.nightly-review.plist`: добавлено `USER=vk` в `EnvironmentVariables`.
- `bin/nightly-review.zsh`:
  - `status` → `rc`;
  - запасной вариант `export USER="${USER:-$(id -un)}"`;
  - промпт передаётся через stdin (`print -r -- "$PROMPT" | claude -p ...`), так что `claude`
    не будет ждать на открытом stdin;
  - stderr `claude` пишется в `nightly-review-ДАТА.err`, хвост этого файла попадает в
    уведомление о сбое (раньше сообщение отсылало к пустому `.md`);
  - в лог пишутся время и длительность каждого запуска;
  - код выхода 0 с пустым результатом считается сбоем и тоже даёт уведомление;
  - если упал сам `notify.sh`, это фиксируется в `nightly-review.err` и не проходит молча.
- `bin/notify.sh`: `curl --fail`. Без этого флага ошибка Telegram API (например, неверный
  токен, HTTP 401/400) возвращала 0 и тоже ничего не оставляла в логах.

Проверка (в песочнице с поддельными `claude`/`notify.sh`, в пустом окружении `env -i`, как у launchd):
сбой → уведомление «FAILED … Not logged in»; успех → «done: …»; пустой вывод с кодом 0 →
«FAILED: empty output». Синтаксис: `zsh -n`, `bash -n` и `plutil -lint` проходят.

## Что сделать на настоящей машине (я ничего не запускал и не отправлял)

```sh
launchctl bootout gui/$UID/com.vk.nightly-review
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist
launchctl kickstart -k gui/$UID/com.vk.nightly-review
launchctl print gui/$UID/com.vk.nightly-review | grep -E 'runs|last exit'
```
Потом проверить, что в Telegram пришло сообщение, `nightly-review-ДАТА.md` свежий и не пустой,
а в `nightly-review.out` указана правдоподобная длительность (не пара секунд). Затем один раз
сломать скрипт специально (например, поставить неверный `REPO`) и убедиться, что пришло
уведомление о сбое. Если `notify.sh` под launchd не сможет прочитать токен из связки ключей
(`security find-generic-password`), это теперь будет видно в `nightly-review.err`.

## Что пригодилось из заметки коллеги

- **Пригодилось:** сначала проверить, запускалась ли задача (`launchctl print`: runs/last exit code), и
  прочитать StandardErrorPath, а не строить теории; ловушка zsh `status=$?` → `rc=$?` (у меня
  ровно та же ошибка, она и сделала сбой невидимым); `USER` в `EnvironmentVariables` против
  «Not logged in» (у меня ровно эта ошибка в логе); промпт через stdin; запись длительности
  запуска; мысль, что exit code 0 ещё не значит, что работа сделана (поэтому проверяю, что вывод не пустой);
  план проверки: kickstart + реальный результат + намеренный сбой.
- **Не пригодилось / не моя ситуация:** ошибка «Input must be provided either through stdin or
  as a prompt argument» в моём логе не встречается, так что промпт через stdin я перевёл для
  надёжности, а не потому, что это была причина. Отдельный `< /dev/null` не нужен, раз
  промпт теперь идёт через stdin. Совет про watchdog, который выходит с 0 по таймауту, ко мне
  не относится: watchdog в моей задаче нет. Ссылку на внешнюю статью я не открывал.
