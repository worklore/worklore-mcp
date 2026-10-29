# Причины сбоя задачи launchd и их исправление

## 1. Причины, почему задача молчала и ничего не сообщала

Анализ логов (`Library/Logs/nightly-review.err`) и конфигурации (`launchctl-print.txt`, `.plist`, скриптов) выявил две основные проблемы:

1. **Ошибка аутентификации CLI (`Not logged in · Please run /login`)**:
   - Задача запускается через launchd как LaunchAgent. В блоке `EnvironmentVariables` в `Library/LaunchAgents/com.vk.nightly-review.plist` была задана только переменная `PATH`.
   - Переменная окружения `USER` отсутствовала. Из-за отсутствия `$USER` в окружении headless CLI (`claude`) не мог получить доступ к учетным данным в macOS Keychain и падал с ошибкой `Not logged in · Please run /login`.

2. **Аварийное завершение скрипта до вызова уведомления (`read-only variable: status`)**:
   - В скрипте `bin/nightly-review.zsh` код завершения команды сохранялся строкой `status=$?`.
   - В оболочке `zsh` переменная `status` является встроенной переменной только для чтения (read-only alias для `$?`).
   - Попытка присваивания `status=$?` приводила к фатальной ошибке zsh: `/Users/vk/bin/nightly-review.zsh:19: read-only variable: status` с немедленным аварийным завершением работы скрипта.
   - В результате блок отправки уведомления об ошибке (`"$NOTIFY" "nightly review FAILED..."`) никогда не выполнялся («вестник умирал раньше, чем успевал сообщить о проблеме»).

Дополнительно: при передаче промпта аргументом `-p "$PROMPT"` в headless-окружении launchd процессу необходим закрытый stdin (`< /dev/null`), чтобы избежать зависания на чтении дескриптора ввода.

---

## 2. Какие части заметки коллеги пригодились

Из предложенной заметки пригодились следующие пункты:
- **`status=$?` в zsh**: подтвердилось прямо по логам (`Library/Logs/nightly-review.err: read-only variable: status`). Заменено на `rc=$?`.
- **Переменная `USER` в `EnvironmentVariables` plist**: `launchctl print` показал, что в окружении сервиса передавался только `PATH`. Без `USER` headless CLI не видит сессию/keychain и завершается с `Not logged in`.
- **`< /dev/null` для stdin**: добавлено перенаправление ввода при вызове `claude -p`, чтобы избежать ожидания ввода в launchd.
- **Диагностический подход**: проверка `runs` и `last exit code` через `launchctl print`, а также чтение `StandardErrorPath` логов до построения догадок.

Не потребовалось / пропущено:
- Передача промпта через pipe (`print -r -- "$PROMPT" | claude -p ...`), так как аргумент `-p "$PROMPT"` с `< /dev/null` работает корректно и не требует переписывания структуры вызова.

---

## 3. Внесенные исправления

1. **`Library/LaunchAgents/com.vk.nightly-review.plist`**:
   - В словарь `EnvironmentVariables` добавлена переменная `USER` со значением `vk` (пользователь согласно путям в plist и launchctl).

2. **`bin/nightly-review.zsh`**:
   - Присваивание `status=$?` заменено на `rc=$?` и обновлены последующие проверки (`$rc`).
   - К вызову `claude` добавлено перенаправление `< /dev/null`.
