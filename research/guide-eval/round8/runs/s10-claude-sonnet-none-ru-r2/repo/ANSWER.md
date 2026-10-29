# Что сделано

Все 6 событий из `docs/EVENTS.md` отправляются через `Analytics.capture`.

- `lib/screens/registration_screen.dart`
  - `registration_email_started` / `registration_phone_started` — один раз за визит на экран, при первом введённом символе (не на каждое нажатие клавиши).
  - `loan_amount_changed` (`amount`) — в `onChangeEnd` слайдера, т.е. итоговое значение после отпускания, а не каждый тик перетаскивания.
  - `terms_accepted` — только при установке галочки (снятие не отправляется).
  - `registration_continue_tapped` (`amount`, `terms`) — по нажатию Continue.
- `lib/screens/offer_screen.dart`
  - `offers_scrolled` (`offset`) — по `ScrollEndNotification`, т.е. раз на завершённый жест прокрутки, а не на каждый кадр.

Решения: частоту событий ограничил осознанно, так как проект на бесплатном тарифе PostHog (см. README). Email и телефон в свойства не передаются (PII). События просмотра экранов не добавлял — они уже идут автоматически.

Не проверено: Flutter/Dart-сборка и тесты не запускались (не уверен, что SDK есть в окружении); ничего не коммитилось и не деплоилось.
