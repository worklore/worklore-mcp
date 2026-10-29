# Отчет о внедрении событий аналитики

В соответствии с требованиями из `docs/EVENTS.md`, были реализованы события аналитики на экранах регистрации (`RegistrationScreen`) и списка предложений (`OfferScreen`) через вызов `Analytics.capture`.

## Реализованные события

1. **`registration_email_started`**
   - **Где**: `lib/screens/registration_screen.dart`
   - **Условие**: Отправляется один раз при начале ввода email пользователя (`text.isNotEmpty`).
   - **Свойства**: Без свойств (PII не передается).

2. **`registration_phone_started`**
   - **Где**: `lib/screens/registration_screen.dart`
   - **Условие**: Отправляется один раз при начале ввода номера телефона пользователя (`text.isNotEmpty`).
   - **Свойства**: Без свойств (PII не передается).

3. **`loan_amount_changed`**
   - **Где**: `lib/screens/registration_screen.dart`
   - **Условие**: Отправляется при перемещении слайдера выбора суммы займа (`Slider.onChanged`).
   - **Свойства**: `{'amount': int}` (округленное выбранное значение суммы).

4. **`terms_accepted`**
   - **Где**: `lib/screens/registration_screen.dart`
   - **Условие**: Отправляется, когда пользователь отмечает чекбокс условий и соглашений (переход из `false` в `true`).
   - **Свойства**: Без свойств.

5. **`registration_continue_tapped`**
   - **Где**: `lib/screens/registration_screen.dart`
   - **Условие**: Отправляется при нажатии на кнопку «Continue» перед переходом на экран предложений.
   - **Свойства**: `{'amount': int, 'terms': bool}`.

6. **`offers_scrolled`**
   - **Где**: `lib/screens/offer_screen.dart`
   - **Условие**: Отправляется при скролле списка предложений (через `NotificationListener<ScrollEndNotification>`).
   - **Свойства**: `{'offset': double}` (текущее смещение прокрутки `notification.metrics.pixels`).

## Проверка
- Код проверен с помощью `flutter analyze`, предупреждений и ошибок нет.
