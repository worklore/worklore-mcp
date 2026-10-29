# Почему nightly-review ни разу ничего не прислал

## Что видно в снимке

- `launchctl-print.txt`: `runs = 6`, `last exit code = 1`. launchd запускал задачу
  каждую ночь с 13 по 18 октября, plist и расписание в порядке.
- `Library/Logs/nightly-review.err` — каждый запуск оставил по две строки:
  ```
  Not logged in · Please run /login
  /Users/vk/bin/nightly-review.zsh:19: read-only variable: status
  ```
- `nightly-review.out` пустой. Скрипт до `notify.sh` ни разу не дошёл, поэтому
  в Telegram не пришло вообще ничего.

## Причина 1 (из-за неё нет даже сообщения об ошибке): `status` в zsh — read-only

В zsh `$status` — встроенный read-only синоним `$?`. Строка 19
`status=$?` вызывает ошибку `read-only variable: status`, и zsh тут же
завершает скрипт с кодом 1. Это и есть `last exit code = 1`. Ветки
`if [ $status -ne 0 ]` с уведомлением о сбое и финальный `notify` так ни разу
и не выполнились. Воспроизводится одной командой:
`zsh -c 'true; status=$?; echo after'` → `read-only variable: status`.
В bash это работало бы, поэтому вручную/в bash ошибку легко не заметить.

**Исправление:** переменная переименована в `rc`.

## Причина 2 (почему сама проверка коммитов падала): `claude` не авторизован под launchd

`claude -p` выходил с ошибкой `Not logged in · Please run /login`. launchd
запускает `/bin/zsh скрипт` как неинтерактивную оболочку: `~/.zshrc` и
`~/.zprofile` не читаются, окружение — только то, что в plist (`PATH`). Если
в терминале авторизация приходит из окружения шелла (например,
`ANTHROPIC_API_KEY` или `CLAUDE_CODE_OAUTH_TOKEN` в `~/.zshrc`) или из
связки ключей, которая в 02:30 недоступна/заблокирована, ночной процесс
ничего из этого не видит.

**Исправление:** скрипт теперь подхватывает файл `~/.config/nightly-review.env`
(если он есть) и экспортирует переменные из него. Что сделать один раз руками:

```sh
claude setup-token            # выдаст долгоживущий токен
mkdir -p ~/.config
printf 'CLAUDE_CODE_OAUTH_TOKEN=%s\n' '<токен>' > ~/.config/nightly-review.env
chmod 600 ~/.config/nightly-review.env
```

Туда же можно положить `TG_BOT_TOKEN=...`. `notify.sh` уже берёт его из
окружения и в связку ключей не лезет. Это страховка на случай, если ночью
связка тоже недоступна (иначе `security find-generic-password` упадёт, и
уведомление снова не уйдёт).

## Остальное, что исправлено в `bin/nightly-review.zsh`

- **Сбой виден в самом уведомлении.** stderr `claude` пишется в
  `~/Library/Logs/nightly-review-ГГГГ-ММ-ДД.err`, и последние 300 байт
  попадают в текст сообщения о сбое. Раньше там была ссылка на `$OUT`, а он
  при ошибке пустой. Копия stderr по-прежнему идёт в общий `nightly-review.err`.
- **Страховка от «молчаливой смерти».** `TRAPEXIT` отправляет
  «script aborted unexpectedly», если скрипт завершился, не дойдя до
  штатного уведомления (ошибка zsh, сигнал и т.п.). Проверка PID нужна,
  чтобы ловушку не запускали подоболочки `$(...)`.
- **Сбой `notify.sh` больше не теряется:** он пишется в stderr, а значит,
  в лог.
- **Права инструментов в headless-режиме.** `claude -p` не может спросить
  разрешения, поэтому `git log/show/diff` без явного разрешения были бы
  отклонены. Добавлен `--allowedTools` только с инструментами для чтения
  (`Read`, `Grep`, `Glob`, `Bash(git log/show/diff:*)`). Это ещё и
  гарантирует «Do not modify any file». stdin берётся из `/dev/null`.

plist менять не нужно, перезагружать агент тоже: launchd каждый раз
запускает скрипт заново с диска.

## Проверка

Скрипт прогнан локально с фейковым `HOME` и заглушками `claude`/`notify.sh`
(в Telegram ничего не отправлялось):

| сценарий | результат |
|---|---|
| `claude` → «Not logged in», exit 1 | `nightly review FAILED (exit 1): Not logged in · Please run /login` |
| `claude` успешно | `nightly review done: …`, exit 0 |
| нет репозитория | `nightly review: repo missing (…)` |
| `claude` нет в PATH | `FAILED (exit 127): … command not found: claude` |
| скрипт падает на ошибке zsh (вставлен `status=1`) | `script aborted unexpectedly …` |
| `notify.sh` сам падает | в stderr/лог: `notify.sh failed (exit 7) for: …` |

Чтобы проверить на реальной машине, не дожидаясь ночи (после создания env-файла):
`launchctl kickstart gui/$UID/com.vk.nightly-review`.
