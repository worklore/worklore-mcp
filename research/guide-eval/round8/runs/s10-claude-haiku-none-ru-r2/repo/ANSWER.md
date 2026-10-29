# Аналитика: события воронки регистрации

Реализованы все шесть событий из `docs/EVENTS.md`. Отправка идёт через существующую обёртку `Analytics.capture` (`lib/analytics.dart`), сама обёртка не менялась.

## Что сделано

### `lib/screens/registration_screen.dart`

| Событие | Где | Свойства |
|---|---|---|
| `registration_email_started` | `onChanged` поля Email | — |
| `registration_phone_started` | `onChanged` поля Phone | — |
| `loan_amount_changed` | `onChangeEnd` слайдера | `amount` (int) |
| `terms_accepted` | `onChanged` чекбокса, когда он включён | — |
| `registration_continue_tapped` | `onPressed` кнопки Continue, перед переходом на `/offers` | `amount` (int), `terms` (bool) |

- `registration_email_started` и `registration_phone_started` отправляются один раз на каждый показ экрана: при первом непустом вводе. Для этого есть флаги `_emailStarted` и `_phoneStarted`.
- Email и телефон в свойства не попадают (PII).

### `lib/screens/offer_screen.dart`

| Событие | Где | Свойства |
|---|---|---|
| `offers_scrolled` | `ScrollEndNotification` у `ListView` | `offset` (double) |

## Решения, которые стоит проверить

1. **`loan_amount_changed` шлётся в `onChangeEnd`, а не в `onChanged`.** `onChanged` срабатывает на каждом шаге перетаскивания, и это сотни событий за одно движение. По описанию в доке нужно итоговое «выбранное» значение, и README упоминает free tier PostHog. Если нужны все промежуточные значения, замените на `onChanged`.
2. **`offers_scrolled` шлётся один раз по окончании прокрутки**, а не на каждом кадре. `offset` равен `metrics.pixels`, то есть абсолютной позиции прокрутки, а не длине пройденного пути. Если в дашборде нужна дельта, это стоит поменять.
3. **`registration_continue_tapped` шлётся только когда кнопка активна.** Неактивная кнопка не реагирует на нажатия, поэтому `terms` в этом событии всегда `true`. Если нужны попытки нажать при неполной форме, понадобится отдельная обработка тапа.

## Проверка

- `dart format`: файлы отформатированы (один файл переформатирован, `registration_screen.dart`).
- `flutter analyze`: `No issues found!`
- Тестов в проекте нет, поэтому автоматических тестов на события я не добавлял.
- В PostHog события не проверялись на реальном устройстве. Ключ в `lib/analytics.dart` остаётся заглушкой `phc_REPLACE_ME_IN_CI`, и его заменяет CI. Сеть для отправки здесь не использовалась.
- Во время `flutter pub get` сгенерировались `.dart_tool/` и `pubspec.lock`, а `analysis_options.yaml` был изменён. Всё это откатено, в рабочем дереве остались только два изменённых файла экранов.

## Что осталось

- В `README.md` написано, что «экраны пока не отправляют события». После этих изменений строка устарела. Я её не трогал, её можно обновить отдельно.
- Изменения не закоммичены.
