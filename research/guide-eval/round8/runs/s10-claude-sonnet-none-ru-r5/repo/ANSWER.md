# Аналитика: что сделано

Все 6 событий из `docs/EVENTS.md` отправляются через `Analytics.capture`.

**registration_screen.dart**
- `registration_email_started` / `registration_phone_started` — один раз за визит, при первом непустом вводе.
- `loan_amount_changed` (`amount`: int) — в `onChangeEnd` слайдера, т.е. один раз за перетаскивание, а не на каждый тик (бесплатный тариф PostHog).
- `terms_accepted` — только при установке галочки (снятие не шлёт).
- `registration_continue_tapped` (`amount`: int, `terms`: bool) — при нажатии Continue.

**offer_screen.dart**
- `offers_scrolled` (`offset`: double) — один раз за визит, когда первая прокрутка закончилась (`ScrollEndNotification`). Экран стал `StatefulWidget` ради флага.

Email и телефон в свойства не передаются (PII). Просмотры экранов не трогал.

`dart format` прошёл; `flutter analyze` не удалось выполнить — зависимости не установлены (нужен `pub get`, т.е. сеть).
