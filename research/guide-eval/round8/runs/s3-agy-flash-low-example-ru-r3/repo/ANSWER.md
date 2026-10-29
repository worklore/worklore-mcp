# Причины сбоя и молчания задачи launchd

В ходе анализа логов (`Library/Logs/nightly-review.err`), конфигурации launchd (`Library/LaunchAgents/com.vk.nightly-review.plist`), скрипта (`bin/nightly-review.zsh`) и диагностического вывода `launchctl print` были обнаружены две взаимосвязанные проблемы, из-за которых задача завершалась с ошибкой и не отправляла уведомления.

---

## 1. Выявленные причины

1. **Ошибка авторизации CLI-агента (`Not logged in · Please run /login`)**:
   - В `com.vk.nightly-review.plist` в блоке `EnvironmentVariables` была задана переменная `PATH`, но отсутствовала переменная окружения `USER`.
   - При запуске через `launchd` переменная `$USER` не устанавливается автоматически в окружении процесса. Утилите `claude` (и обращению к macOS Keychain) требуется `$USER` для поиска учетных данных/сессии, поэтому вызов завершался с ошибкой `Not logged in · Please run /login`.

2. **Падение скрипта до отправки уведомления об ошибке (`read-only variable: status`)**:
   - В `bin/nightly-review.zsh` на строке 19 выполнялось присваивание `status=$?`.
   - В оболочке `zsh` переменная `status` является встроенной и доступной только для чтения (read-only, алиас к `$?`). Попытка присвоить ей значение приводит к фатальной ошибке zsh: `/Users/vk/bin/nightly-review.zsh:19: read-only variable: status`.
   - Из-за этого выполнение скрипта аварийно прерывалось прямо перед блоком проверки статуса и вызовом `bin/notify.sh`. В результате уведомление о падении ни разу не отправлялось.

3. **Потенциальное зависание на `stdin` при запуске под launchd**:
   - Когда аргумент передается как `-p "$PROMPT"` в неинтерактивном окружении launchd без закрытого ввода, CLI может ожидать ввода на stdin.

---

## 2. Что было исправлено

1. **`Library/LaunchAgents/com.vk.nightly-review.plist`**:
   - В `EnvironmentVariables` добавлена переменная:
     ```xml
     <key>USER</key>
     <string>vk</string>
     ```
     Теперь CLI-агент видит пользователя и может получить доступ к своим учетным данным в Keychain.

2. **`bin/nightly-review.zsh`**:
   - Заменена зарезервированная переменная `status` на `rc`:
     ```zsh
     rc=$?
     if [ $rc -ne 0 ]; then
       "$NOTIFY" "nightly review FAILED (exit $rc), see $OUT"
       exit $rc
     fi
     ```
   - Добавлен закрытый ввод `< /dev/null` для вызова `claude`:
     ```zsh
     claude -p "$PROMPT" --output-format text < /dev/null > "$OUT"
     ```

---

## 3. Какие части заметки коллеги пригодились

Из заметки коллеги пригодились следующие пункты:

1. **Проблема с переменной `status` в `zsh`**:
   - *"In zsh, status is a read-only built-in variable, and assigning to it kills the script on the spot. That assignment sat between the agent call and the failure-notification call."*
   - Полностью совпало с ошибкой строки 19 в `bin/nightly-review.zsh` и объяснило "идеальное молчание". Пригодилась рекомендация использовать имя переменной `rc=$?`.

2. **Отсутствие `USER` в `EnvironmentVariables` plist-файла**:
   - *"set USER under EnvironmentVariables in the plist so a headless CLI can reach its keychain login"* / *"set USER in the plist's EnvironmentVariables, or the CLI can't find its login in the keychain and dies with 'Not logged in'"*.
   - Полностью совпало с ошибкой `Not logged in · Please run /login` в логе `nightly-review.err`.

3. **Закрытие stdin (`< /dev/null`) при передаче промпта аргументом**:
   - *"give it a closed stdin (< /dev/null) when the prompt is an argument, or it waits on stdin"*.
   - Использовано для предотвращения зависания `claude` под launchd.

### Что пропущено / не понадобилось:
- Передача промпта через stdin (`print -r -- "$PROMPT" | claude ...`), так как в данном скрипте промпт передается через флаг аргумента `-p "$PROMPT"`, для которого достаточно явного перенаправления ввода `< /dev/null`.
- Команды `launchctl kickstart` и живой перезапуск сервиса, так как работа велась со снимком директории без реального деплоя во внешнюю систему.
