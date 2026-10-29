# Реализация аналитики

- На экране регистрации добавлены события `registration_email_started` и `registration_phone_started` при первом вводе в соответствующее поле за время открытия экрана. Email и телефон не передаются в свойствах.
- При изменении суммы отправляется `loan_amount_changed` с целочисленным `amount`; при установке флажка — `terms_accepted`.
- Нажатие доступной кнопки Continue отправляет `registration_continue_tapped` с `amount` (int) и `terms` (bool).
- Прокрутка списка предложений отправляет `offers_scrolled` с текущим `offset` (double).
- Все события отправляются через существующий `Analytics.capture`.

Проверка: `dart format` выполнен. `flutter analyze --no-pub` не прошёл, поскольку в этой рабочей директории не разрешены зависимости Flutter, `posthog_flutter` и `flutter_lints`.
