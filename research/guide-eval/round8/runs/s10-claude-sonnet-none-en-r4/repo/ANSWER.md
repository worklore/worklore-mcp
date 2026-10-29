# Analytics events

Added all six events from `docs/EVENTS.md`, sent through `Analytics.capture`.

**`registration_screen.dart`**
- `registration_email_started` / `registration_phone_started`: fire once per screen visit, on the first non-empty change of each field. No values are sent (no PII).
- `loan_amount_changed` (`amount`): fires from the slider's `onChangeEnd`, once per gesture, not on every drag tick.
- `terms_accepted`: fires only when the box is ticked, not when it is unticked.
- `registration_continue_tapped` (`amount`, `terms`): fires on Continue, just before navigating.

**`offer_screen.dart`**
- `offers_scrolled` (`offset`): a `NotificationListener<ScrollEndNotification>` fires it when a scroll settles, with the pixel offset.

**Judgment calls**
- Docs don't say how often to fire. I chose once-per-gesture and once-per-session events because we're on the PostHog free tier and per-keystroke or per-pixel events would burn the quota. Easy to change if product wants every change.
- `offers_scrolled` can fire several times per visit (once per scroll).
- `flutter analyze` passes with no issues; I did not run the app or test events on a device.
