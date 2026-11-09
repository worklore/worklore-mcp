# Что сделано

Все события из `docs/EVENTS.md` подключены через существующую обёртку `Analytics.capture`.

## Экран регистрации

В `lib/screens/registration_screen.dart` добавлены события:

- `registration_email_started` — при первом вводе email на экране;
- `registration_phone_started` — при первом вводе телефона на экране;
- `loan_amount_changed` — при изменении суммы слайдером, со свойством `amount` типа `int`;
- `terms_accepted` — при включении checkbox согласия с условиями;
- `registration_continue_tapped` — при нажатии Continue, со свойствами `amount` (`int`) и `terms` (`bool`), перед переходом к предложениям.

Email и номер телефона в аналитику не передаются.

## Экран предложений

В `lib/screens/offer_screen.dart` к списку подключён `ScrollController`. При прокрутке отправляется `offers_scrolled` со свойством `offset` типа `double`. Контроллер освобождается в `dispose`.

## Проверка

- `git diff --check` выполнен успешно.
- `dart format` и `flutter analyze --no-pub` не удалось выполнить: система запретила запуск локальных исполняемых файлов Dart и Flutter с ошибкой `Operation not permitted`.
- Тестовых файлов в проекте нет.
