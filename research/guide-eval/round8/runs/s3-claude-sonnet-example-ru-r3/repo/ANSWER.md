# Почему nightly-review молчала

Задача **запускалась** каждую ночь (`launchctl-print.txt`: `runs = 6`, `last exit code = 1`; в `.err` шесть повторов). Молчание — это два слоя багов:

1. **`claude -p` падал с "Not logged in · Please run /login".** В окружении launchd нет `USER`
   (в `environment` только PATH и XPC_SERVICE_NAME), и CLI не находит свой логин в keychain.
   Исправление: в plist в `EnvironmentVariables` добавлен `USER=vk`.
2. **`status=$?` в zsh убивал скрипт.** `status` — read-only переменная zsh
   (`nightly-review.zsh:19: read-only variable: status`). Скрипт умирал до вызова `notify.sh`,
   поэтому уведомление об ошибке не уходило. Исправление: `rc=$?`.

## Дополнительно изменено в скрипте
- `claude ... < /dev/null` — закрытый stdin, чтобы CLI не ждал ввода.
- В stdout-лог пишется код возврата и длительность запуска.
- Нулевой код при пустом выводе считается ошибкой (rc=2) и порождает уведомление.
- Длительность добавлена в тексты уведомлений.

## Какие части заметки коллеги пригодились
- Пригодились: сначала доказать, что задача запускалась (`launchctl print`: runs/last exit code);
  читать stderr-лог; не присваивать `status` в zsh; `USER` в EnvironmentVariables; `< /dev/null`;
  логировать длительность; не считать нулевой код и пустой результат успехом.
- Не пригодились: передача промпта через stdin (у вас ошибки про промпт нет, промпт передаётся аргументом
  и ошибка была в логине); догадка «задача не запускается» — тут она запускалась.

## Не проверено
Я ничего не запускал (нет вашего macOS/keychain, внешних отправок не делал). Проверьте у себя:
`launchctl bootout gui/$UID/com.vk.nightly-review; launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist; launchctl kickstart -k gui/$UID/com.vk.nightly-review`,
затем убедитесь, что `last exit code = 0`, файл `nightly-review-<дата>.md` свежий и непустой, запуск
длился не секунды, а в Telegram пришло сообщение. Затем один раз намеренно сломайте скрипт и проверьте
уведомление об ошибке. Если «Not logged in» останется, выполните `claude /login` под этим пользователем.
Также README говорит 02:30, как и plist.
