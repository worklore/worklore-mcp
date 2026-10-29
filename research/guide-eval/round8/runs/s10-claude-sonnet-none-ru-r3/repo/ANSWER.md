# Аналитика: что сделано

Все события отправляются через `Analytics.capture`. Изменены `lib/screens/registration_screen.dart` и `lib/screens/offer_screen.dart` (`OfferScreen` стал `StatefulWidget`).

| Событие | Реализация |
|---|---|
| `registration_email_started` | один раз за визит, при первом непустом вводе в email |
| `registration_phone_started` | то же для телефона |
| `loan_amount_changed` | `Slider.onChangeEnd` (а не `onChanged`), `amount` = округлённое int |
| `terms_accepted` | только при установке галочки (снятие не шлётся) |
| `registration_continue_tapped` | при нажатии Continue, `amount` (int), `terms` (bool) |
| `offers_scrolled` | один раз за визит, по окончанию первого скролла, `offset` = `metrics.pixels` (double) |

Решения:
- Слайдер, скролл и ввод текста порождают десятки вызовов в секунду; мы на бесплатном тарифе PostHog, поэтому события отправляются по окончании жеста / один раз. Для воронки этого достаточно.
- Email и телефон в свойства не передаются (PII).
- Просмотры экранов не трогал (их шлёт `PosthogObserver`).
- Не проверял: сборку и `flutter analyze`/тесты не запускал (проверьте локально).
