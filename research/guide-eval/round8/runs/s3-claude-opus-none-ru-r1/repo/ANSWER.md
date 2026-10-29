# Почему nightly-review молчал

## Что показывают улики

- `launchctl-print.txt`: `runs = 6`, `last exit code = 1`, т.е. launchd честно
  запускал задачу каждую ночь с 13 по 18 октября. Плист, расписание и PATH в порядке
  (`claude` находится, иначе было бы `command not found`).
- `Library/Logs/nightly-review.err` — шесть одинаковых пар строк:
  ```
  Not logged in · Please run /login
  /Users/vk/bin/nightly-review.zsh:19: read-only variable: status
  ```

## Причина 1 (главная, почему не было даже сообщения об ошибке): `status=$?` в zsh

В zsh `status` — встроенная **read-only** переменная (синоним `$?`). Строка 19
`status=$?` — это ошибка `read-only variable: status`, и неинтерактивный zsh
на ней **прерывает скрипт с кодом 1**. До блока `if [ $status -ne 0 ]` и до
вызова `notify.sh` выполнение не доходит ни в успешном, ни в неуспешном случае.
Поэтому Telegram не получил ни сводки, ни «FAILED». (В bash этот код работал бы,
отсюда и ловушка.) Проверено: `zsh -c 'true; status=$?; echo after'` → `read-only
variable: status`, exit 1.

**Исправление:** переменная переименована в `rc`.

## Причина 2 (почему сам ревью падал): `claude` под launchd не авторизован

`claude -p` пишет `Not logged in · Please run /login`. Под launchd задача не
читает `~/.zshrc`/`~/.zprofile`, поэтому то, что в терминале даёт авторизацию
(например, `ANTHROPIC_API_KEY`/`CLAUDE_CODE_OAUTH_TOKEN`, экспортированные в
профиле), здесь отсутствует; кроме того, в 02:30 связка ключей login может быть
заблокирована, и сохранённые в Keychain учётные данные недоступны. Что именно из
двух — по снимку не определить (в нём нет `~/.claude` и rc-файлов), но лечится
одинаково.

**Что нужно сделать вручную (один раз):**
```sh
claude setup-token            # выдаст долгоживущий токен подписки
mkdir -p ~/.config/nightly-review
cat > ~/.config/nightly-review/env <<'EOF'
export CLAUDE_CODE_OAUTH_TOKEN=...   # токен из setup-token
export TG_BOT_TOKEN=...              # чтобы не зависеть от Keychain ночью
EOF
chmod 600 ~/.config/nightly-review/env
```
Скрипт теперь подхватывает этот файл, если он есть.

## Причина 3 (скрытая, могла бы проглотить и исправленное уведомление): `notify.sh`

- `: "${TG_BOT_TOKEN:=$(security ...)}"` — провал `security` (заблокированный
  keychain ночью) **не** срабатывает на `set -e`: токен становится пустым, скрипт
  идёт дальше.
- `curl -sS` без `-f` возвращает 0 даже на HTTP 401/404 от Telegram, а ответ
  уходит в `/dev/null`. То есть неудачная отправка выглядела как успешная.
- «Работает вручную», потому что в интерактивной сессии keychain разблокирован
  (или `TG_BOT_TOKEN` задан в окружении shell).

**Исправление:** явная проверка результата `security`, `curl --fail-with-body`,
текст ошибки Telegram печатается в stderr, ненулевой код выхода.

## Прочие улучшения в `bin/nightly-review.zsh`

- stderr `claude` пишется в `nightly-review-ДАТА.err`, и начало ошибки
  включается в Telegram-сообщение `FAILED` (раньше в сообщении была бы только
  ссылка на пустой `.md`).
- Если не удалась сама отправка в Telegram, это пишется в
  `~/Library/Logs/nightly-review.err` и показывается локальным уведомлением macOS —
  больше никаких «тихих» провалов.
- В `-p` режиме некому подтверждать разрешения, поэтому read-only инструменты
  (`git log/show/diff`, Read, Grep, Glob) разрешены через `--allowedTools`;
  иначе ревью не смог бы даже прочитать историю коммитов.

## Проверка

Скрипт прогнан с заглушками `claude`/`notify.sh` в чистом окружении (`env -i`,
как у launchd):
- `claude` падает с «Not logged in» → отправляется `nightly review FAILED (exit 1): Not logged in …`;
- `claude` успешен → отправляется `nightly review done: …`;
- `notify.sh` падает → запись в stderr-лог + локальное уведомление.

Реальная отправка в Telegram и запуск `claude` не выполнялись. Плист менять не
нужно; после правки скриптов перезагрузка агента не требуется (launchd запускает
файл заново каждый раз). Проверить вручную можно так:
`launchctl kickstart gui/$UID/com.vk.nightly-review`.
