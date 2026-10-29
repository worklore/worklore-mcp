# Причины сбоя и отсутствия уведомлений

## 1. Почему ничего не приходило в Telegram
В скрипте `bin/nightly-review.zsh` на строке 19 происходила попытка присвоить значение специальной переменной:
```zsh
status=$?
```
В оболочке **zsh** имя `status` является встроенным read-only псевдонимом для переменной `$?` (код завершения предыдущей команды). При попытке присвоения zsh завершает работу скрипта с фатальной ошибкой:
```
nightly-review.zsh:19: read-only variable: status
```
Из-за этого скрипт аварийно завершался ещё до выполнения блока проверки ошибок:
```zsh
if [ $status -ne 0 ]; then
  "$NOTIFY" "nightly review FAILED (exit $status), see $OUT"
  exit $status
fi
```
и вызов `bin/notify.sh` ни при успешном, ни при ошибочном выполнении команды `claude` никогда не происходил.

## 2. Почему команда `claude` завершалась с ошибкой
Судя по логу `Library/Logs/nightly-review.err`:
```
Not logged in · Please run /login
```
CLI-утилита `claude` не авторизована (отсутствует активная сессия/ключ в окружении запуска задачи). Поэтому `claude` завершалась с ненулевым кодом выхода, после чего скрипт сразу падал на присвоении `status=$?`.

---

## Что было исправлено
1. В `bin/nightly-review.zsh` переменная `status` переименована в `exit_code`:
   ```zsh
   claude -p "$PROMPT" --output-format text > "$OUT"
   exit_code=$?

   if [ $exit_code -ne 0 ]; then
     "$NOTIFY" "nightly review FAILED (exit $exit_code), see $OUT"
     exit $exit_code
   fi
   ```
   Теперь при любой ошибке (включая неавторизованный `claude`) управление корректно доходит до блока отправки уведомления об ошибке в Telegram через `bin/notify.sh`.

## Что требуется сделать пользователю в рабочей системе
- Авторизовать `claude` (выполнить вход `claude /login` или передать необходимые переменные окружения, например `ANTHROPIC_API_KEY`, через `EnvironmentVariables` в `.plist` либо в скрипте).
