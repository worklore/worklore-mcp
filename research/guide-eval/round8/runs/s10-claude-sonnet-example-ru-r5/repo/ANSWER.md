# Аналитика: что сделано

Все 6 событий из `docs/EVENTS.md` отправляются через `Analytics.capture`, имена и свойства как в спеке. Email и телефон в свойства не попадают.

## registration_screen.dart
- `registration_email_started`, `registration_phone_started`: один раз за визит экрана, при первом изменении поля (флаги `_emailStartedFired`, `_phoneStartedFired` в состоянии экрана).
- `loan_amount_changed` (`amount`): в `onChangeEnd` слайдера, один раз за перетаскивание. `onChanged` только обновляет UI.
- `terms_accepted`: при установке галочки (при снятии не отправляется).
- `registration_continue_tapped` (`amount`, `terms`): при нажатии Continue.

## offer_screen.dart
- Экран стал `StatefulWidget`, чтобы хранить флаг.
- `offers_scrolled` (`offset` = `metrics.pixels`): из `NotificationListener<ScrollEndNotification>`, один раз за визит экрана.

## Что пригодилось из заметки коллеги
Нужен был именно этот приём: события «started» и «changed» нельзя вешать на каждый `onChanged`, иначе уйдёт событие на каждое нажатие клавиши/шаг слайдера, а у нас бесплатный тариф PostHog. Использовано: флаги «один раз за визит» для текстовых полей, `onChangeEnd` для слайдера, `ScrollEndNotification` для скролла (плюс флаг). Фокус-листенеры не понадобились: финальные значения не нужны. Остальное (debug-проверка, grep) к задаче не относилось.

## Не проверено
Сборка и запуск не выполнялись (Flutter/dart в окружении не проверял), тесты не запускались.
