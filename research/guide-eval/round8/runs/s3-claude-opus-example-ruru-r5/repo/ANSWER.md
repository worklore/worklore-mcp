# Почему nightly-review молчал

## Факты (до всяких теорий)

- `launchctl-print.txt`: `runs = 6`, `last exit code = 1`, `state = waiting`.
  То есть launchd **запускал** задачу каждую ночь. Проблема не в расписании.
- `Library/Logs/nightly-review.err` содержит одни и те же две строки на каждый из 6 запусков:
  ```
  Not logged in · Please run /login
  /Users/vk/bin/nightly-review.zsh:19: read-only variable: status
  ```

## Причины (их две, одна поверх другой)

1. **`claude` не залогинен под launchd.** В окружении задачи (блок `environment`
   в `launchctl print`) есть только `PATH` и `XPC_SERVICE_NAME`, а `USER` нет.
   Без `USER` CLI не находит свою запись в keychain и падает с «Not logged in».
   При запуске вручную из терминала `USER` задан, поэтому там всё работает.
   Это сама ошибка.

2. **`status=$?` убивает скрипт до отправки уведомления.** В zsh `status` —
   встроенная переменная только для чтения (синоним `$?`). Присваивание ей
   завершает неинтерактивный скрипт с кодом 1 (проверено: `zsh -c 'status=1; echo after'`
   печатает `read-only variable: status`, `after` не выводится, код выхода 1).
   Строка 19 стоит между вызовом `claude` и вызовом `notify.sh`, поэтому
   уведомление об ошибке никогда не отправлялось. Отсюда полная тишина: и
   отчёт, и уведомление об ошибке умирали. Отсюда же `last exit code = 1`.

`notify.sh` ни разу не вызывался, поэтому в логе от него ничего нет. Работает ли
он под launchd (ему нужен `security find-generic-password` из keychain), пока
не проверено. Новый скрипт это покажет (см. ниже).

## Что исправлено

`Library/LaunchAgents/com.vk.nightly-review.plist`:
- в `EnvironmentVariables` добавлены `USER=vk` (и на всякий случай `HOME=/Users/vk`).

`bin/nightly-review.zsh`:
- `status=$?` → `rc=$?`.
- Промпт передаётся через stdin (`print -r -- "$PROMPT" | claude -p ...`), а
  не многострочным аргументом. Так stdin не остаётся открытым и нет вопросов с
  разбором аргумента.
- stderr от `claude` пишется в `nightly-review-YYYY-MM-DD.md.err`, а его хвост
  попадает в текст уведомления об ошибке.
- Функция `notify` дублирует каждое сообщение в stderr (→ `nightly-review.err`) и
  записывает в лог, если сам `notify.sh` упал. Так сломанный уведомитель тоже не
  даёт полной тишины.
- Пишутся время старта, `USER` и длительность запуска. Запуск headless-агента
  длиной в пару секунд означает, что он упал на старте.
- Код выхода 0 при пустом выводе считается ошибкой (exit 2 + уведомление).
  «Зелёный» код без сделанной работы больше не проходит молча.

Локальная проверка с заглушками `claude`/`notify.sh` (без сети): сценарии
«claude падает», «exit 0, но пустой вывод» и «успех» отправляют уведомление
(FAILED / FAILED / done) и выходят с кодами 1 / 2 / 0.

## Что сделать на самом Mac (я этого не запускал)

```sh
launchctl bootout gui/$UID/com.vk.nightly-review
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist
launchctl kickstart -k gui/$UID/com.vk.nightly-review
launchctl print gui/$UID/com.vk.nightly-review | grep -E 'runs|last exit'
tail ~/Library/Logs/nightly-review.err
```
Проверить: `last exit code = 0`, файл `nightly-review-<дата>.md` свежий и
непустой, длительность правдоподобная (не 0–2 с), сообщение «done» пришло в
Telegram. Затем один раз намеренно сломать запуск (например, временно поставить
`REPO` на несуществующий путь) и убедиться, что пришло «FAILED». Если в
`.err` появится `notify.sh failed`, значит, `security` не может прочитать
токен под launchd. Тогда разбираться с keychain/`TG_BOT_TOKEN`.

## Что пригодилось из заметки коллеги

- **Пригодилось:**
  - Сначала смотреть `launchctl print` (runs / last exit code) и лог из
    `StandardErrorPath`, а не строить теорию «launchd не запускает».
  - Баг с `status=$?` в zsh: ровно тот же, исправлен на `rc=$?`.
  - Ловушка из поправки (через статью Пердума): `USER` в `EnvironmentVariables`,
    иначе «Not logged in». Это наша первопричина.
  - Ставить сообщение об ошибке так, чтобы его ничего не перекрывало,
    логировать длительность и проверять реальный результат, а не только код
    выхода. Отсюда проверка на пустой вывод.
  - План проверки: kickstart, затем намеренная поломка.
- **Частично:** передача промпта через stdin. Ошибки «Input must be provided…»
  у нас в логе нет, так что это не наша причина. Сделано как профилактика: заодно
  закрывает вопрос «claude ждёт stdin», и `< /dev/null` не нужен.
- **Не пригодилось:** история про 16:50 и сторожевой таймер с выходом 0 по
  тайм-ауту (у нас таймера нет). Сама мысль «exit 0 ≠ работа сделана» учтена.
