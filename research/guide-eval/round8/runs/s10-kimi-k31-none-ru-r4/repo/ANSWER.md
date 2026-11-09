# События аналитики

Реализованы все события из `docs/EVENTS.md` через существующую обёртку `Analytics.capture`.

## Экран регистрации

В `lib/screens/registration_screen.dart` добавлены:

- `registration_email_started` — однократно при первом непустом вводе email;
- `registration_phone_started` — однократно при первом непустом вводе телефона;
- `loan_amount_changed` — при изменении слайдера, с целочисленным параметром `amount`;
- `terms_accepted` — при установке флага согласия с условиями, без события при его снятии;
- `registration_continue_tapped` — перед переходом к предложениям, с параметрами `amount` (int) и `terms` (bool).

Email и номер телефона в свойства событий не передаются.

## Экран предложений

В `lib/screens/offer_screen.dart` список обёрнут в `NotificationListener`. При прокрутке отправляется `offers_scrolled` с параметром `offset` (double), содержащим текущее смещение списка в пикселях.

Автоматические события просмотра экранов не дублировались.

## Проверка

- `git diff --check` выполнен успешно.
- `flutter analyze` и проверка форматирования через `dart format --output=none --set-exit-if-changed` не смогли запуститься: операционная система вернула `Operation not permitted` (код 126) для исполняемых файлов Flutter и Dart.
- Тестовые файлы в проекте отсутствуют, поэтому автоматические тесты не запускались.
