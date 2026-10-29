# Отчёт о причинах молчания задачи launchd и внесённых исправлениях

## 1. Причины, почему задача launchd ни разу ничего не сообщила

Анализ логов (`Library/Logs/nightly-review.err`), конфигурации launchd (`Library/LaunchAgents/com.vk.nightly-review.plist`) и скрипта (`bin/nightly-review.zsh`) выявил две последовательные ошибки:

1. **Ошибка авторизации Claude CLI под launchd (`Not logged in · Please run /login`)**:
   - Задача launchd запускается в минимальном окружении, где по умолчанию в секции `EnvironmentVariables` была задана только переменная `PATH`.
   - Переменная окружения `USER` не была передана в `EnvironmentVariables`. Вследствие этого headless CLI `claude` не мог определить пользователя и получить сохранённые учетные данные / токен из macOS Keychain, завершая работу с ошибкой:
     ```
     Not logged in · Please run /login
     ```

2. **Падение zsh-скрипта из-за присваивания встроенной переменной `status` (`read-only variable: status`)**:
   - Сразу после вызова `claude` в строке 19 скрипта `bin/nightly-review.zsh` выполнялось присваивание:
     ```zsh
     status=$?
     ```
   - В оболочке `zsh` переменная `status` является встроенной переменной только для чтения (синоним `$?`). Попытка присвоить ей значение приводит к фатальной ошибке выполнения скрипта:
     ```
     /Users/vk/bin/nightly-review.zsh:19: read-only variable: status
     ```
   - Скрипт аварийно завершался в этой точке, не доходя до проверки `if [ $status -ne 0 ]` и вызова `"$NOTIFY" "nightly review FAILED ..."`. В результате бот в Telegram не получал уведомление даже об ошибке.

---

## 2. Какие части заметки коллеги пригодились

Из заметки коллеги пригодились следующие наблюдения и рекомендации:

1. **Проверка присваивания `status` в zsh**:
   - Рекомендация использовать `rc=$?` вместо `status=$?`, так как `status` в `zsh` доступна только для чтения и присваивание убивает скрипт на месте до блока отправки уведомления об ошибке.
2. **Передача переменной `USER` в `EnvironmentVariables` plist-файла**:
   - Указание на то, что без `USER` headless CLI не может получить доступ к keychain и падает с сообщением «Not logged in».
3. **Передача промпта через stdin**:
   - Передача многострочного промпта в `claude` через пайп (`print -r -- "$PROMPT" | claude -p ...`), чтобы избежать проблем с обработкой ввода при неинтерактивном запуске.

### Что не относилось к текущей проблеме / было пропущено:
- Совет про `< /dev/null` для аргументов: не требуется, так как промпт теперь передаётся напрямую через stdin.
- Команды деплоя/перезапуска сервиса через `launchctl bootstrap/kickstart` были опущены в соответствии с правилом работать только локально внутри текущей директории и ничего не деплоить.

---

## 3. Что было исправлено

1. **`bin/nightly-review.zsh`**:
   - Заменено присваивание `status=$?` на `rc=$?` (и соответственно обращение к `$rc` в условиях и уведомлениях).
   - Вызов `claude` переведён на передачу промпта через stdin:
     ```zsh
     print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"
     rc=$?

     if [ $rc -ne 0 ]; then
       "$NOTIFY" "nightly review FAILED (exit $rc), see $OUT"
       exit $rc
     fi
     ```
2. **`Library/LaunchAgents/com.vk.nightly-review.plist`**:
   - В словарь `EnvironmentVariables` добавлена переменная `USER` со значением `vk`:
     ```xml
     <key>EnvironmentVariables</key>
     <dict>
       <key>PATH</key>
       <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
       <key>USER</key>
       <string>vk</string>
     </dict>
     ```
