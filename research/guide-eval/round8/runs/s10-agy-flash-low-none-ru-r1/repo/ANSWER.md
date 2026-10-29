# Реализация событий аналитики

В соответствии со спецификацией в `docs/EVENTS.md`, были реализованы все события аналитики воронки регистрации с использованием существующей обёртки `Analytics.capture`.

## Реализованные события

1. **`registration_email_started`** (`lib/screens/registration_screen.dart`):
   - Отправляется при начале ввода email пользователем (при первом непустом вводе).
   - Не передает PII (email не отправляется в свойствах события).

2. **`registration_phone_started`** (`lib/screens/registration_screen.dart`):
   - Отправляется при начале ввода телефона пользователем (при первом непустом вводе).
   - Не передает PII (номер телефона не отправляется в свойствах события).

3. **`loan_amount_changed`** (`lib/screens/registration_screen.dart`):
   - Отправляется через коллбек `onChangeEnd` у виджета `Slider`, когда пользователь завершает перемещение ползунка суммы займа.
   - Свойства: `amount` (`int`, округленное значение суммы займа).

4. **`terms_accepted`** (`lib/screens/registration_screen.dart`):
   - Отправляется при установке чекбокса согласия с условиями (`CheckboxListTile`) в значение `true`.
   - Без дополнительных свойств.

5. **`registration_continue_tapped`** (`lib/screens/registration_screen.dart`):
   - Отправляется при нажатии на кнопку «Continue» («Продолжить»).
   - Свойства: `amount` (`int`), `terms` (`bool`).

6. **`offers_scrolled`** (`lib/screens/offer_screen.dart`):
   - Отправляется при завершении скролла списка предложений с помощью `NotificationListener<ScrollNotification>` (`ScrollEndNotification`).
   - Свойства: `offset` (`double`, текущее смещение скролла `metrics.pixels`).
