# Analytics events

Added all six events from `docs/EVENTS.md` via `Analytics.capture`.

**registration_screen.dart**
- `registration_email_started` / `registration_phone_started`: sent once per screen visit, on the first non-empty change (not per keystroke).
- `loan_amount_changed`: sent from the slider's `onChangeEnd` (once per drag) with `amount` as int.
- `terms_accepted`: sent only when the box becomes ticked (not on untick).
- `registration_continue_tapped`: sent on Continue with `amount` (int) and `terms` (bool).

**offer_screen.dart**
- `offers_scrolled`: sent on `ScrollEndNotification` (once per scroll gesture) with `offset` (double).

Choices: since we're on the PostHog free tier, I avoided per-keystroke, per-slider-tick and per-pixel events. No email/phone values are sent. Nothing was run or tested against PostHog; `flutter` analysis/tests were not run.
