# Реализация аналитики

- На экране регистрации добавлены `registration_email_started` и `registration_phone_started` при первом вводе в соответствующее поле. Адрес и номер не передаются.
- При изменении суммы отправляется `loan_amount_changed` с целым `amount`; при установке флажка — `terms_accepted`; при нажатии Continue — `registration_continue_tapped` с целым `amount` и логическим `terms`.
- На экране предложений при первой прокрутке пользователем отправляется `offers_scrolled` с `offset` типа `double`.
- Все события отправляются через существующий `Analytics.capture`.

Проверка: `flutter analyze --no-pub` завершился без замечаний после локального `flutter pub get --offline`. Созданные при проверке служебные файлы удалены.
