# Почему задача молчала

Задача работала, но молчала по двум независимым причинам — из-за второй даже
сообщение об ошибке не уходило. Доказательства: `launchctl print` показывает
`runs = 6`, `last exit code = 1` (запускалась каждую ночь и падала), а в
`Library/Logs/nightly-review.err` — ровно 12 строк: 6 запусков × 2 ошибки.

## Причина 1: скрипт умирал раньше, чем отправлял сообщение об ошибке

`Library/Logs/nightly-review.err`:

```
Not logged in · Please run /login
/Users/vk/bin/nightly-review.zsh:19: read-only variable: status
```

В zsh `status` — встроенная **read-only** переменная (синоним `$?`). Строка
`status=$?` в `bin/nightly-review.zsh:19` выдавала ошибку, и неинтерактивный
zsh **завершал весь скрипт** на этом месте. Ветка
`"nightly review FAILED (exit ...)"` никогда не выполнялась — поэтому ни одно
сообщение об ошибке не дошло до Telegram.

**Исправлено:** переменная переименована в `rc` (плюс добавлены проверки
`command -v claude` и EXIT-trap как страховка: при любом неожиданном падении
скрипт всё равно попытается отправить уведомление).

## Причина 2: claude не аутентифицирован в контексте launchd

Каждый из 6 запусков claude падал с `Not logged in · Please run /login`.
Интерактивный логин (`claude /login`) в фоновой ночной задаче невозможен:
OAuth-токен Claude Code живёт в связке ключей текущего сеанса и для фонового
процесса может быть недоступен (блокировка связки ключей ночью/после сна,
ACL элемента ключей). Из терминала всё «работает руками», из launchd — нет.

**Исправлено:** скрипт теперь берёт Anthropic API key из связки ключей
(по аналогии с тем, как `notify.sh` достаёт токен Telegram) и экспортирует
его как `ANTHROPIC_API_KEY` — для headless-запуска этого достаточно, и логин
не нужен. Секрет не прописан ни в скрипте, ни в plist.

Перед первым запуском нужно один раз создать элемент ключницы (в терминале,
на своей машине):

```bash
security add-generic-password -s anthropic-api-key -a "$USER" -w '<Anthropic API key>'
```

## Дополнительно

- В plist добавлены `HOME` и `USER` в `EnvironmentVariables` — раньше
  окружение задачи содержало только `PATH`, что ломает инструменты,
  рассчитывающие на домашнюю директорию (launchd не всегда выставляет их
  так, как интерактивный shell).
- Оставшийся риск: если в 02:30 Mac спит, запуск откладывается до пробуждения,
  а если при этом связка ключей заблокирована (например, после перезагрузки),
  `security find-generic-password` не сработает и уведомления тоже не уйдут.
  Проверить можно, отправив задачу вручную:
  `launchctl kickstart gui/$UID/com.vk.nightly-review`

## Что изменено

- `bin/nightly-review.zsh` — `rc` вместо `status`, ключ из связки ключей для
  claude, проверка наличия `claude`, EXIT-trap с гарантированным уведомлением.
- `Library/LaunchAgents/com.vk.nightly-review.plist` — добавлены `HOME`/`USER`.

## Как применить у себя (на своей машине, вручную)

1. Скопировать исправленные `bin/nightly-review.zsh` и plist в свои `~/bin` и
   `~/Library/LaunchAgents/`.
2. Создать элемент ключницы `anthropic-api-key` (команда выше).
3. Перезагрузить агент:
   `launchctl bootout gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist`
   затем
   `launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist`
4. Проверить без ожидания ночи:
   `launchctl kickstart gui/$UID/com.vk.nightly-review`
