# Что сделано

Реализованы все события из `docs/EVENTS.md` через существующую обёртку `Analytics.capture`.

- `lib/screens/registration_screen.dart`
  - `registration_email_started` — один раз при первом вводе email.
  - `registration_phone_started` — один раз при первом вводе телефона.
  - `loan_amount_changed` — при изменении суммы, с целочисленным свойством `amount`.
  - `terms_accepted` — при установке флажка согласия с условиями.
  - `registration_continue_tapped` — при нажатии Continue, со свойствами `amount` (int) и `terms` (bool).
  - Email и номер телефона в свойства событий не передаются.
- `lib/screens/offer_screen.dart`
  - `offers_scrolled` — при прокрутке списка, со свойством `offset` (double), содержащим текущее смещение.

Дополнительные события просмотра экранов не добавлялись: они уже отслеживаются автоматически.

# Проверка

`git diff --check` прошёл без ошибок. Запустить `dart format` и `flutter analyze` не удалось: система запретила выполнение локальных бинарников Dart/Flutter с ошибкой `Operation not permitted` (код 126). В проекте нет существующих тестов.
