# Аналитика: что сделано

Все 6 событий из `docs/EVENTS.md` отправляются через `Analytics.capture`, имена совпадают с документом.

**registration_screen.dart**
- `registration_email_started` / `registration_phone_started` — при первом введённом символе, один раз за визит на экран (иначе событие шло бы на каждое нажатие клавиши).
- `loan_amount_changed` (`amount` int) — в `onChangeEnd` слайдера, т.е. один раз после окончания перетаскивания, а не на каждый кадр (экономия квоты бесплатного тарифа PostHog).
- `terms_accepted` — только когда галочку поставили (снятие не отправляется).
- `registration_continue_tapped` (`amount` int, `terms` bool) — при нажатии Continue.

**offer_screen.dart**
- Экран стал `StatefulWidget`. `offers_scrolled` (`offset` double) отправляется один раз за визит, когда прокрутка остановилась и offset > 0.

PII: email и телефон в свойствах не отправляются. Просмотры экранов не трогал (уже трекаются автоматически).

Не проверялось: `dart format` / сборка / тесты не запускались (проверьте `flutter analyze` локально).
