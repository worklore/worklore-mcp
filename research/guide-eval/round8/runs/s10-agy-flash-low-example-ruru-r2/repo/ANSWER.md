# Реализация событий аналитики

Были реализованы продуктовые события аналитики из `docs/EVENTS.md` с использованием обёртки `Analytics.capture`.

## 1. Что сделано

### Экран регистрации (`lib/screens/registration_screen.dart`)
1. **`registration_email_started`**: отправляется при начале ввода email (по первому изменению непустого поля с защитой через флаг `_emailStartedFired`, чтобы не спамить на каждое нажатие клавиши).
2. **`registration_phone_started`**: отправляется при начале ввода телефона (по первому изменению непустого поля с защитой через флаг `_phoneStartedFired`).
3. **`loan_amount_changed`**: отправляется в коллбэке `onChangeEnd` у `Slider` с параметром `amount` (`int`, округлённое значение `_amount.round()`), чтобы событие отправлялось один раз при отпускании слайдера, а не на каждый шаг движения.
4. **`terms_accepted`**: отправляется при включении чекбокса условий соглашения (`newValue == true`).
5. **`registration_continue_tapped`**: отправляется при нажатии кнопки «Continue» с параметрами `amount` (`int`) и `terms` (`bool`).

### Экран списка предложений (`lib/screens/offer_screen.dart`)
6. **`offers_scrolled`**: отправляется по завершении прокрутки списка (`ScrollEndNotification` через `NotificationListener<ScrollEndNotification>`) со свойством `offset` (`double`, `notification.metrics.pixels`), предотвращая отправку на каждое микрообновление скролла.

---

## 2. Какие части заметки коллеги пригодились

Из заметки коллеги пригодились рекомендации по предотвращению исчерпания квоты аналитических событий:

- **Текстовые поля (пункт 2 заметки):** добавление булевых флагов в состояние экрана (`_emailStartedFired` и `_phoneStartedFired`), благодаря чему события `registration_email_started` и `registration_phone_started` отправляются только один раз при старте ввода пользователем, а не на каждый введенный символ в `onChanged`.
- **Слайдер (пункт 5 заметки):** перенос отправки аналитики для ползунка кредита в коллбэк `onChangeEnd` вместо `onChanged`. Коллбэк `onChanged` оставлен исключительно для перерисовки значения в UI (`setState`), а `loan_amount_changed` отправляется единожды при завершении перемещения ползунка.
- **Скролл списка (пункт 6 заметки):** использование `NotificationListener<ScrollEndNotification>` вместо отслеживания каждого смещения через `ScrollController` или `ScrollUpdateNotification`. Событие `offers_scrolled` срабатывает один раз при завершении жеста скролла с передачей итогового `offset`.
