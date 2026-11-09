# События аналитики

Реализованы все события из `docs/EVENTS.md` через существующую обёртку `Analytics.capture`.

## Экран регистрации

В `lib/screens/registration_screen.dart` добавлены:

- `registration_email_started` — однократно при первом непустом вводе email;
- `registration_phone_started` — однократно при первом непустом вводе телефона;
- `loan_amount_changed` — при изменении слайдера, с целочисленным свойством `amount`;
- `terms_accepted` — при установке флага согласия, без события при его снятии;
- `registration_continue_tapped` — при нажатии Continue, со свойствами `amount` (int) и `terms` (bool).

Значения email и телефона в аналитику не передаются.

## Экран предложений

В `lib/screens/offer_screen.dart` список обёрнут в `NotificationListener<ScrollNotification>`. При обновлениях прокрутки отправляется `offers_scrolled` со свойством `offset` (double), равным текущему `metrics.pixels`.

## Проверка

- `git diff --check` выполнен успешно.
- `dart format` и `flutter analyze` запустить не удалось: операционная система блокирует исполнение обоих бинарников с ошибкой `Operation not permitted` (код 126). Поэтому форматирование и статический анализ средствами Flutter/Dart не подтверждены.

Новые зависимости не добавлялись, внешние сервисы напрямую не вызывались.
