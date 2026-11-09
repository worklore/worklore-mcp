# Что сделано

- На экране регистрации через существующую обёртку `Analytics.capture` добавлены события:
  - `registration_email_started` — один раз при первом вводе email;
  - `registration_phone_started` — один раз при первом вводе телефона;
  - `loan_amount_changed` — при изменении суммы, со свойством `amount` типа `int`;
  - `terms_accepted` — при установке флажка согласия с условиями;
  - `registration_continue_tapped` — при нажатии Continue, со свойствами `amount` (`int`) и `terms` (`bool`).
- На экране предложений добавлено событие `offers_scrolled` при прокрутке списка. В свойстве `offset` передаётся текущее смещение типа `double`.
- Email и телефон в свойства событий не передаются. Автоматические события просмотра экранов не изменялись.

## Проверка

- `git diff --check` выполнен успешно.
- `dart format` и `flutter analyze --no-pub` запустить не удалось: окружение запрещает выполнение установленных бинарных файлов Dart и Flutter с ошибкой `Operation not permitted` (код 126).
