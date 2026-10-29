# Почему nightly-review молчала

Задача запускалась (`runs = 6`, `last exit code = 1`) — launchd исправен. Тишина из-за двух наложившихся багов (лог `nightly-review.err` это показывает):

1. **`Not logged in · Please run /login`** — под launchd в окружении нет `USER`, `claude` не находит свой логин в keychain и завершается с ошибкой. Из-за этого обзор ни разу не сделан.
2. **`nightly-review.zsh:19: read-only variable: status`** — в zsh `status` встроенная переменная только для чтения. Присваивание `status=$?` убивало скрипт сразу после падения `claude`, до вызова `notify.sh`. Поэтому уведомления об ошибке не было — репортёр умирал раньше, чем говорил.

## Исправления
- `bin/nightly-review.zsh`: `status` → `rc`; вызов `claude` получил `< /dev/null`.
- `LaunchAgents/com.vk.nightly-review.plist`: в `EnvironmentVariables` добавлен `USER=vk`.
- После правки plist нужно перезагрузить: `launchctl bootout gui/501/com.vk.nightly-review && launchctl bootstrap gui/501 ~/Library/LaunchAgents/com.vk.nightly-review.plist`, затем проверка `launchctl kickstart -k gui/501/com.vk.nightly-review`. Здесь я этого не запускал (это снимок).

## Что пригодилось из заметки коллеги
- Сначала `launchctl print` + чтение лога (запуски были, код 1).
- Ловушка `status` в zsh → `rc=$?`.
- `USER` в `EnvironmentVariables` (причина «Not logged in»).
- `< /dev/null` при передаче промпта аргументом.

## Что не применялось
- Передача промпта через stdin: в логе нет ошибки «Input must be provided», промпт аргументом доходит, так что не причина.
- Время запуска 16:50 из заметки — у меня расписание 02:30; логирование длительности не добавлял.
- Проверка уведомления об ошибке: рекомендую один раз намеренно сломать скрипт (например, неверный `REPO`) и убедиться, что пришло сообщение. Также стоит проверить, что `security find-generic-password` в `notify.sh` работает в контексте launchd — не проверено.
