# Реализация аналитики

- На экране регистрации через `Analytics.capture` добавлены события `registration_email_started` и `registration_phone_started` при первом вводе, `loan_amount_changed` при изменении слайдера, `terms_accepted` при установке флажка и `registration_continue_tapped` при нажатии Continue.
- На экране предложений добавлено `offers_scrolled` после завершения прокрутки, если смещение изменилось. Передаётся итоговое смещение в `offset` типа `double`.
- В свойствах передаются только указанные в `docs/EVENTS.md` значения: `amount` типа `int` и `terms` типа `bool`. Email и телефон не передаются.

Проверка: `flutter analyze --no-pub` завершился без замечаний после локального `flutter pub get --offline`. Внешние сервисы не вызывались.
