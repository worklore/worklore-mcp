# Реализация событий аналитики

В соответствии со спецификацией из `docs/EVENTS.md` были реализованы все события аналитики воронки регистрации и экрана предложений с использованием обёртки `Analytics.capture`.

## Реализованные события

1. **`registration_email_started`**
   - **Экран:** `lib/screens/registration_screen.dart`
   - **Условие отправки:** Пользователь начал ввод email (отправляется единожды при первом непустом вводе в поле).
   - **Параметры:** без параметров (PII не передается).

2. **`registration_phone_started`**
   - **Экран:** `lib/screens/registration_screen.dart`
   - **Условие отправки:** Пользователь начал ввод номера телефона (отправляется единожды при первом непустом вводе в поле).
   - **Параметры:** без параметров (PII не передается).

3. **`loan_amount_changed`**
   - **Экран:** `lib/screens/registration_screen.dart`
   - **Условие отправки:** Изменение значения на слайдере суммы займа (`onChanged`).
   - **Параметры:** `amount` (`int`, округленная сумма через `v.round()`).

4. **`terms_accepted`**
   - **Экран:** `lib/screens/registration_screen.dart`
   - **Условие отправки:** Пользователь установил чекбокс согласия с условиями (`_terms` переходит из `false` в `true`).
   - **Параметры:** без параметров.

5. **`registration_continue_tapped`**
   - **Экран:** `lib/screens/registration_screen.dart`
   - **Условие отправки:** Пользователь нажал кнопку «Continue».
   - **Параметры:**
     - `amount` (`int`): выбранная сумма займа (`_amount.round()`).
     - `terms` (`bool`): статус принятия условий (`_terms`).

6. **`offers_scrolled`**
   - **Экран:** `lib/screens/offer_screen.dart`
   - **Условие отправки:** Завершение скролла списка предложений через `NotificationListener<ScrollNotification>` (`ScrollEndNotification`).
   - **Параметры:** `offset` (`double`: текущая позиция скролла `notification.metrics.pixels`).
