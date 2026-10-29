# Аналитика: что сделано

Все 6 событий из `docs/EVENTS.md` отправляются через `Analytics.capture`, имена совпадают с документом.

**`registration_screen.dart`**
- `registration_email_started` / `registration_phone_started`: один раз за визит на экран, при первом непустом вводе.
- `loan_amount_changed` (`amount` int): в `onChangeEnd` слайдера, то есть один раз за жест, а не на каждый кадр перетаскивания (экономим квоту бесплатного тарифа PostHog).
- `terms_accepted`: только когда галочку поставили (снятие не отправляется).
- `registration_continue_tapped` (`amount` int, `terms` bool): при нажатии Continue, перед переходом.

**`offer_screen.dart`**
- `offers_scrolled` (`offset` double): по `ScrollEndNotification`, когда прокрутка остановилась, а не на каждое изменение позиции.

Email и телефон в свойства не передаются (PII). Просмотры экранов не трогал.

`flutter analyze`: ошибок нет.
