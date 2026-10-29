# Почему nightly-review ни разу ничего не прислал

## Что видно по снимку

- `launchctl-print.txt`: `runs = 6`, `last exit code = 1`. С 12 по 18 октября задача
  запускалась каждую ночь, то есть launchd и расписание работают.
- `Library/Logs/nightly-review.err` содержит одну и ту же пару строк на каждый запуск:
  ```
  Not logged in · Please run /login
  /Users/vk/bin/nightly-review.zsh:19: read-only variable: status
  ```
- `nightly-review.out` пуст. В лог не попало ни одной ошибки от `notify.sh`, то есть
  до него дело ни разу не дошло.

## Причина 1: не приходят даже сообщения об ошибке (`status=$?` в zsh)

Скрипт запускается через `/bin/zsh`. В zsh `status` — это **встроенная read-only
переменная** (синоним `$?`). Строка 19 `status=$?` вызывает ошибку
`read-only variable: status`, и неинтерактивный zsh на ней **сразу обрывает скрипт
с кодом 1**. Ветка `if [ $status -ne 0 ]; then "$NOTIFY" ...` никогда не выполняется.
Поэтому нет ни сводок, ни «FAILED»-сообщений, а `last exit code = 1` берётся от
самого zsh, а не от `claude`. Проверено: `zsh -c 'true; status=$?; echo after'`
печатает ту же ошибку и не доходит до `echo`. (В bash такой код работал бы, видимо,
поэтому ошибку и не заметили.)

## Причина 2: сам `claude` под launchd не авторизован

`Not logged in · Please run /login`: когда `claude` запускается из launchd, он не
видит учётных данных, которые есть в интерактивном терминале. Под launchd
не читаются `~/.zshrc`/`~/.zprofile`, так что `ANTHROPIC_API_KEY` или другие
переменные из профиля туда не попадают. Окружение задачи — только `PATH` из plist.
OAuth-логин из связки ключей в фоновой задаче ночью тоже ненадёжен (связка может
быть заблокирована, сессия может быть другой). Даже без причины 1 вы бы получали только
«FAILED», а не сводку.

## Сопутствующие проблемы (исправлены заодно)

- В режиме `claude -p` инструменты, которым нужно разрешение (в т.ч. `Bash` для
  `git log`), автоматически запрещаются. Агент не смог бы прочитать историю коммитов.
  Теперь явно разрешены только чтение и read-only git:
  `--allowedTools "Bash(git log:*)" "Bash(git show:*)" "Bash(git diff:*)" Read Grep Glob`.
  Заодно это гарантирует «Do not modify any file».
- `notify.sh` вызывал `curl -sS ... > /dev/null` без `--fail`. Ошибка Telegram API
  (неверный токен, chat_id и т.п.) давала код 0, а ответ выбрасывался. Теперь
  `--fail-with-body`, и при ошибке текст ответа пишется в stderr, то есть в
  `nightly-review.err`.

## Что изменено

`bin/nightly-review.zsh`:
- `status` переименован в `rc`.
- Добавлен `trap ... EXIT`: если скрипт оборвётся по любой неожиданной причине, всё
  равно уйдёт уведомление «script aborted unexpectedly».
- Ошибка самого `notify.sh` записывается в лог с отметкой времени, а не теряется.
- Сообщение о провале содержит последние строки `nightly-review.err`, так что
  «Not logged in» будет видно прямо в Telegram.
- Токен Claude берётся явно: из `CLAUDE_CODE_OAUTH_TOKEN`/`ANTHROPIC_API_KEY`, если
  они заданы, иначе из связки ключей (`claude-nightly-token`).

`bin/notify.sh`: `--fail-with-body` и логирование ошибки Telegram.

Проверено на заглушках (`claude`/`notify.sh` подменены, сеть не используется):
ветки «claude упал», «успех» и «нет репозитория» теперь все доходят до уведомления.

## Что нужно сделать вам (вне этой папки я ничего не трогал)

1. Создать долгоживущий токен и положить его в связку ключей:
   ```sh
   claude setup-token
   security add-generic-password -U -s claude-nightly-token -a "$USER" -w '<токен>'
   ```
   Другой вариант: добавить `CLAUDE_CODE_OAUTH_TOKEN` в `EnvironmentVariables` plist,
   но тогда токен будет лежать открытым текстом в файле.
2. Скопировать исправленные `bin/*` в `~/bin/`, затем проверить запуск вручную в
   контексте launchd:
   ```sh
   launchctl kickstart -k gui/$UID/com.vk.nightly-review
   tail ~/Library/Logs/nightly-review.err
   ```
   plist менять не нужно, перезагружать агент тоже.
3. Учтите: если связка ключей заблокирована, `security find-generic-password` в
   `notify.sh` тоже не сработает. Теперь это будет видно в `nightly-review.err`.
