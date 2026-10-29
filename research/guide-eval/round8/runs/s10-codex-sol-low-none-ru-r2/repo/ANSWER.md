# Реализация событий аналитики

На экране регистрации добавлены события из `docs/EVENTS.md` через `Analytics.capture`:

- `registration_email_started` и `registration_phone_started` — при первом непустом вводе в соответствующее поле за время открытия экрана. Адрес и номер не передаются.
- `loan_amount_changed` — при изменении значения ползунка, с целочисленным `amount`.
- `terms_accepted` — при установке флажка условий.
- `registration_continue_tapped` — при нажатии активной кнопки Continue, с целочисленным `amount` и булевым `terms`.

На экране предложений добавлено `offers_scrolled` после завершения прокрутки списка, с `offset` типа `double` в пикселях.

Проверка: `flutter analyze --no-pub` — ошибок нет. Зависимости для проверки разрешены из локального кеша командой `flutter pub get --offline`.
