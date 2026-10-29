# Причины сбоя и отсутствия уведомлений

### 1. Почему не отправлялись уведомления об ошибке
В скрипте `bin/nightly-review.zsh` на строке 19 происходило присваивание:
```zsh
status=$?
```
В оболочке **zsh** переменная `status` является специальным встроенным алиасом (read-only) для `$?` (кода возврата последней команды). При попытке присвоить значение read-only переменной (`status=...`) `zsh` немедленно завершает выполнение скрипта с фатальной ошибкой:
```
/Users/vk/bin/nightly-review.zsh:19: read-only variable: status
```
Из-за этого скрипт аварийно прерывался до выполнения блока проверки `if [ ... ]; then "$NOTIFY" ... fi`, и `bin/notify.sh` ни разу не вызывался.

Логи ошибки (`Library/Logs/nightly-review.err`) это подтверждают:
```
Not logged in · Please run /login
/Users/vk/bin/nightly-review.zsh:19: read-only variable: status
```

---

### 2. Почему вообще падала команда `claude`
Команда:
```zsh
claude -p "$PROMPT" --output-format text > "$OUT"
```
завершалась с ошибкой `Not logged in · Please run /login` (код возврата 1).

Возможные причины:
- Пользователь не авторизован в CLI `claude` (не выполнена команда `claude /login` или `claude auth login`).
- Либо утилита `claude` в неинтерактивном окружении / launchd не имеет доступа к переменной окружения `ANTHROPIC_API_KEY` (или токену доступа).

---

## Что было исправлено

1. **В скрипте `bin/nightly-review.zsh`**:
   - Переменная `status` заменена на `exit_code`.
   - Теперь при падении команды `claude` скрипт не аварийно падает на строке присвоения, а успешно заходит в ветку обработки ошибки и отправляет уведомление через `bin/notify.sh`:
     ```zsh
     exit_code=$?
     if [ $exit_code -ne 0 ]; then
       "$NOTIFY" "nightly review FAILED (exit $exit_code), see $OUT"
       exit $exit_code
     fi
     ```

## Что необходимо сделать пользователю (вне репозитория / на хосте)
1. Авторизоваться в Claude Code под нужным пользователем (`claude login` / `claude auth login`) либо передавать ключ `ANTHROPIC_API_KEY` (например, через секцию `EnvironmentVariables` в `Library/LaunchAgents/com.vk.nightly-review.plist` или в скрипте/keychain).
2. При необходимости обновить зарегистрированный LaunchAgent с помощью:
   ```bash
   launchctl bootout gui/$UID/com.vk.nightly-review
   launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist
   ```
