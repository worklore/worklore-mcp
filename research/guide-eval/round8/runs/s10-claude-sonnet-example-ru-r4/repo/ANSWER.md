# Реализация событий аналитики

Все события из docs/EVENTS.md добавлены через `Analytics.capture`. Имена и свойства совпадают со спецификацией. Email и телефон в свойства не передаются.

**lib/screens/registration_screen.dart**
- `registration_email_started` и `registration_phone_started` отправляются один раз за визит на экран, при первой правке поля. Для этого есть флаги `_emailInputFired` и `_phoneInputFired`.
- `loan_amount_changed` с `amount` (int) отправляется в `onChangeEnd` слайдера, то есть один раз за перетаскивание. `onChanged` только обновляет UI.
- `terms_accepted` отправляется только когда галочку поставили, а не когда сняли.
- `registration_continue_tapped` с `amount` (int) и `terms` (bool) отправляется по нажатию Continue, перед переходом.

**lib/screens/offer_screen.dart**
- Экран стал `StatefulWidget`. `offers_scrolled` с `offset` (double) отправляется из `NotificationListener<ScrollEndNotification>`, один раз за визит и только при смещении больше 0.

## Что пригодилось из заметки коллеги
- Один раз за визит с флагом на текстовых полях: применено.
- `onChangeEnd` вместо `onChanged` для слайдера: применено.
- `ScrollEndNotification` вместо обновлений скролла: применено.
- Без финальных значений полей и без focus-listener'ов: спецификации нужны только события «начал», поэтому эти части пропущены.
- Проверка через `PostHogConfig.debug` и дашборд PostHog не выполнялась. Приложение я не запускал, `flutter analyze` и тесты тоже не гонял.
