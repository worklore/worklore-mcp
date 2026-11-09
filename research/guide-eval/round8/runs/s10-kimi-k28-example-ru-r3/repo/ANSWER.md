# ANSWER

## Что сделано

Реализованы все 6 событий из `docs/EVENTS.md` через существующую обёртку
`Analytics.capture` (`lib/analytics.dart`). Имена событий и свойства совпадают
со спецификацией один в один, значения email/phone не отправляются (PII).

### `lib/screens/registration_screen.dart`

| Событие | Где и когда отправляется | Свойства |
|---|---|---|
| `registration_email_started` | `onChanged` поля email, один раз за визит — флаг `_emailStartedFired` | — |
| `registration_phone_started` | `onChanged` поля phone, один раз за визит — флаг `_phoneStartedFired` | — |
| `loan_amount_changed` | `onChangeEnd` слайдера (после завершения перетаскивания) | `amount` (int) |
| `terms_accepted` | `onChanged` чекбокса, только при установке галочки (не при снятии) | — |
| `registration_continue_tapped` | `onPressed` кнопки Continue, перед навигацией | `amount` (int), `terms` (bool) |

- Флаги «отправлено» живут в `_RegistrationScreenState`, который создаётся
  заново при каждом входе на экран, так что «раз за визит» получается
  естественно.
- `setState(() {})` в текстовых полях сохранён — нужен для пересчёта
  `_canContinue`, как и раньше.

### `lib/screens/offer_screen.dart`

| Событие | Где и когда отправляется | Свойства |
|---|---|---|
| `offers_scrolled` | `NotificationListener<ScrollEndNotification>` над списком — после окончания прокрутки | `offset` (double, `metrics.pixels`) |

## Какие части заметки коллеги пригодились

Заметка оказалась прямо в точку — без неё соблазн повесить `capture` прямо в
`onChanged` привёл бы к тому же исчерпанию квоты PostHog (событие за каждое
нажатие клавиши и каждый шаг слайдера). Использовано:

- **Раздел «The fix» — текстовые поля:** событие отправляется один раз за визит
  по первому изменению, через `bool`-флаг на состоянии экрана
  (`registration_email_started`, `registration_phone_started`). Финальное
  значение как свойство не нужно, поэтому обработчик потери фокса не добавлял.
- **«Sliders»:** событие с `amount` перенесено из `onChanged` в `onChangeEnd`
  (`loan_amount_changed`), `onChanged` оставлен только для обновления UI.
- **«Scrolls»:** `offers_scrolled` отправляется из
  `NotificationListener<ScrollEndNotification>`, а не из обновлений скролла.

Не пригодилось (не было в задаче): пункт про `FocusNode`-листенеры для
tap/focus-событий, шаги «Reproduce this» и проверка через `PostHogConfig.debug`
(тулчейн Flutter в этой среде недоступен — проверка описана ниже). Идея «Keep
event names and properties unchanged» учтена изначально — имена взяты из
`docs/EVENTS.md` дословно.

## Проверка

`flutter analyze` запустить не удалось: SDK лежит в домашней директории
пользователя, из этой среды исполнение бинарников оттуда запрещено
(`Operation not permitted`), системного Flutter/Dart нет. Сделано вместо этого:

- тщательное ручное ревью обоих файлов: сигнатуры колбэков (`ValueChanged<double>`
  у `onChangeEnd`, `ScrollNotificationCallback` у `NotificationListener`),
  типы свойств (`int` через `.round()`, `double` через `metrics.pixels`,
  `bool` для `terms`);
- механическая проверка баланса скобок по трём изменённым/задетым файлам —
  сбалансировано.

Рекомендую после коммита прогнать `flutter analyze` локально и прокликать
сценарий: ввод email в 20 символов → ровно один `registration_email_started`,
один проход слайдера → один `loan_amount_changed`, одна прокрутка списка →
один `offers_scrolled`.
