# Analytics events implementation

All six events from `docs/EVENTS.md` are sent via `Analytics.capture`. No PII is sent as a property.

**lib/screens/registration_screen.dart**
- `registration_email_started` / `registration_phone_started`: fired once, on the first change in each field.
- `loan_amount_changed` (`amount` int): fired from the slider's `onChangeEnd`, so once per drag instead of on every frame (free-tier volume).
- `terms_accepted`: fired only when the box is ticked, not when it is unticked.
- `registration_continue_tapped` (`amount` int, `terms` bool): fired on Continue, before navigating.

**lib/screens/offer_screen.dart**
- `offers_scrolled` (`offset` double): fired on `ScrollEndNotification` (vertical), so once per finished scroll gesture.

Notes
- Decision for you: if `offers_scrolled` should fire only once per session for the funnel, that is a one-line flag. I chose per gesture end because the spec says "how far they scrolled".
- I ran `dart format` only. I did not run the analyzer or the app, because `flutter_lints` isn't resolved here (no `pub get`). Nothing was sent to PostHog.
