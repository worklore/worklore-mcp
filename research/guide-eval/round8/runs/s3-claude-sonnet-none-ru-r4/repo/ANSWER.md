# Почему nightly-review молчал

Задача launchd **запускалась** (в `launchctl-print.txt`: `runs = 6`, `last exit code = 1`), но падала, и сообщить об этом было нечем.

## Причины

1. **`claude` не залогинен в окружении launchd.** В `nightly-review.err` каждый запуск начинается с `Not logged in · Please run /login`. Агент launchd работает без твоей интерактивной сессии и не видит авторизацию, которая есть в терминале. Поэтому `claude -p` завершался с ошибкой.
2. **Баг в скрипте: `status` в zsh — read-only переменная** (`status` — псевдоним `$?`). Строка `status=$?` падала с `read-only variable: status` (строка 19), и скрипт прерывался до ветки `if [ $status -ne 0 ]`. Поэтому `notify.sh` с «FAILED» не вызывался ни разу. Это главная причина полного молчания: даже при падении claude уведомление об ошибке не уходило.
3. Мелочи, из-за которых ошибки тоже могли теряться: stderr от `claude` не попадал в уведомление, пустой вывод считался успехом, а `curl` без `--fail` возвращал 0 при HTTP-ошибке Telegram (4xx), а ответ уходил в `/dev/null`.

`notify.sh` вручную работает, поэтому он не виноват.

## Что исправлено

- `bin/nightly-review.zsh`: переменная `status` заменена на `rc`; stderr claude пишется в `~/Library/Logs/nightly-review-ДАТА.err`, и его начало идёт в сообщение об ошибке; пустой вывод считается ошибкой.
- `bin/notify.sh`: `curl --fail`, чтобы ошибки Telegram давали ненулевой код и попадали в `.err`.

## Что нужно сделать тебе (я не могу это сделать отсюда)

Починить авторизацию для launchd, иначе job будет каждую ночь честно присылать «FAILED: Not logged in». Варианты: выполнить `claude setup-token` и передать токен как `CLAUDE_CODE_OAUTH_TOKEN` (лучше читать из Keychain в скрипте, как сделано для Telegram, а не писать в plist), либо `ANTHROPIC_API_KEY` аналогичным образом. Затем проверить: `launchctl kickstart -k gui/$UID/com.vk.nightly-review`.
