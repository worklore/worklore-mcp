# Почему ночная задача nightly-review молчала

## Что показали логи

`Library/Logs/nightly-review.err` содержит шесть одинаковых пар строк (совпадает с `runs = 6` в `launchctl-print.txt`):

```
Not logged in · Please run /login
/Users/vk/bin/nightly-review.zsh:19: read-only variable: status
```

Задача запускалась по расписанию, так что launchd работал. Молчала сама задача.

## Причины

**1. Уведомление о провале не отправлялось (главная причина тишины).**
Строка 19 исходного скрипта: `status=$?`. В zsh `status` - read-only встроенная переменная, присваивание завершает скрипт. Строка стоит между вызовом `claude` и вызовом `notify.sh` о провале, поэтому скрипт падает раньше, чем может сообщить об ошибке. Воспроизведено локально: скрипт выходит с `read-only variable: status`, уведомлений нет.

**2. Агент не был залогинен под launchd (причина самого провала).**
`claude -p` печатает `Not logged in · Please run /login`. Наиболее вероятная причина: в plist нет переменной `USER`, и CLI не находит логин в keychain. Это гипотеза по аналогии с заметкой коллеги. На этой машине её не проверить: нет `/Users/vk`, нет keychain и launchd-задачи пользователя. Подтвердится она только запуском через `launchctl kickstart` на вашем Mac (см. ниже). Если после правки ошибка останется, следующий шаг - проверить авторизацию CLI из окружения launchd (например, через `ANTHROPIC_API_KEY`, который берётся из keychain).

**3. Уведомитель тоже мог молчать.**
Если `notify.sh` падал (например, keychain недоступен), ошибка уходила в никуда. Теперь она пишется в `.err`.

**4. Успех без работы считался успехом.**
Если `claude` возвращал 0 и пустой вывод, скрипт отправлял `done: ` с пустым текстом. Теперь пустой вывод - провал.

## Что изменено

- `bin/nightly-review.zsh`:
  - `status` заменён на `rc`; это единственное место, где падал скрипт.
  - `claude` получает `< /dev/null`, чтобы не ждать stdin.
  - Пишется строка `exit=... duration=...s` в stderr (попадает в `.err`).
  - Провал = ненулевой exit ИЛИ пустой вывод; в сообщении указаны оба значения.
  - Функция `notify` при ошибке отправки пишет в stderr.
- `Library/LaunchAgents/com.vk.nightly-review.plist`: добавлен `USER` = `vk` в `EnvironmentVariables`. Имя `vk` взято из путей `/Users/vk`; перед установкой проверьте `id -un`.

## Проверка

Локально (zsh, подменённые `claude` и `notify.sh`, временный HOME внутри рабочей папки, папка после проверки удалена):

- успех: `done` отправлен, exit 0;
- `claude` с exit 1: `FAILED`, exit 1 (скрипт больше не падает на `status`);
- exit 0 с пустым выводом: `FAILED (exit 0, output empty)`, exit 1;
- `notify.sh` падает: ошибка записана в stderr, exit 1;
- нет папки репозитория: `repo missing`.

`plutil -lint` для plist: OK. `zsh -n` для скрипта: OK.

**Не проверено:** реальный launchd, keychain, Telegram. Это нужно сделать на вашей машине.

## Что сделать на Mac

```sh
cp bin/nightly-review.zsh ~/bin/
cp Library/LaunchAgents/com.vk.nightly-review.plist ~/Library/LaunchAgents/
launchctl bootout gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist
launchctl kickstart -k gui/$UID/com.vk.nightly-review
launchctl print gui/$UID/com.vk.nightly-review | grep -E 'runs|last exit'
tail -n 5 ~/Library/Logs/nightly-review.err
ls -la ~/Library/Logs/nightly-review-*.md
```

Ожидаемо: `last exit code = 0`, в `.err` строка `claude exit=0 duration=...s` с разумным временем (не несколько секунд), свежий `nightly-review-<дата>.md` непустой, и пришло сообщение `done` в Telegram.

Затем проверка провала: временно поставьте в скрипте заведомо неверный путь к `claude` или сломайте `REPO`, сделайте `kickstart` и убедитесь, что пришло `FAILED`. Потом верните скрипт.

## Что из заметки коллеги пригодилось

- **`rc=$?` вместо `status`** - это та же ошибка, что и у вас, точно подтверждена `.err`.
- **`< /dev/null` при передаче промпта аргументом** - применено.
- **`USER` в `EnvironmentVariables`** - применено как самая вероятная причина «Not logged in».
- **Не доверять одному exit code, проверять реальный результат и длительность** - применено: пустой вывод считается провалом, длительность пишется в лог.
- **Тест провала намеренной поломкой** - включён в шаги проверки.
- **Уведомление как можно ближе к началу провала** - сделано через функцию `notify` сразу после ошибки.

## Что не пригодилось или не применено

- **Передача промпта через stdin** - не нужно: промпт передаётся аргументом, и в логе нет ошибки `Input must be provided`. Менять не стал.
- **`launchctl print` как доказательство работы** - у вас уже был снимок, и он подтвердил, что задача запускалась (`runs = 6`, `exit 1`). Но сам по себе exit code не доказывает, что работа выполнена; поэтому добавлена проверка результата.
- **Ссылка на статью Mihai Perdum (семь сбоев)** - не открывал и не опирался на неё; использовал только то, что есть в тексте заметки.
