# Реализация событий аналитики воронки регистрации

В соответствии со спецификацией [docs/EVENTS.md](docs/EVENTS.md) реализованы все события аналитики с использованием обёртки `Analytics.capture(...)`:

1. **`registration_email_started`** ([lib/screens/registration_screen.dart](lib/screens/registration_screen.dart)):
   - Отправляется один раз при начале ввода email пользователем (когда поле впервые становится непустым).
   - Свойства: без свойств (PII не передаётся).

2. **`registration_phone_started`** ([lib/screens/registration_screen.dart](lib/screens/registration_screen.dart)):
   - Отправляется один раз при начале ввода номера телефона пользователем (когда поле впервые становится непустым).
   - Свойства: без свойств (PII не передаётся).

3. **`loan_amount_changed`** ([lib/screens/registration_screen.dart](lib/screens/registration_screen.dart)):
   - Отправляется при изменении значения слайдера суммы кредита.
   - Свойства: `{'amount': amount.round()}` (`int`).

4. **`terms_accepted`** ([lib/screens/registration_screen.dart](lib/screens/registration_screen.dart)):
   - Отправляется при установке чекбокса согласия с условиями (когда значение становится `true`).
   - Свойства: без свойств.

5. **`registration_continue_tapped`** ([lib/screens/registration_screen.dart](lib/screens/registration_screen.dart)):
   - Отправляется при нажатии на кнопку «Continue» на экране регистрации.
   - Свойства: `{'amount': _amount.round(), 'terms': _terms}` (`amount` int, `terms` bool).

6. **`offers_scrolled`** ([lib/screens/offer_screen.dart](lib/screens/offer_screen.dart)):
   - Отправляется при скролле списка предложений (`NotificationListener<ScrollNotification>` при `ScrollUpdateNotification`).
   - Свойства: `{'offset': notification.metrics.pixels}` (`double`).
