# Analytics events

All six events from `docs/EVENTS.md` are sent via `Analytics.capture`, with the exact names and properties from the doc. No PII is sent.

**Registration screen** (`lib/screens/registration_screen.dart`)
- `registration_email_started` and `registration_phone_started` fire once, on the first non-empty input in each field.
- `loan_amount_changed` (`amount` as int) fires from the slider's `onChangeEnd`, so once per drag rather than on every tick. This keeps volume down on the PostHog free tier.
- `terms_accepted` fires only when the box becomes ticked, not when it is unticked.
- `registration_continue_tapped` (`amount` as int, `terms` as bool) fires on Continue, before navigation.

**Offers screen** (`lib/screens/offer_screen.dart`)
- `offers_scrolled` (`offset` as double) fires on `ScrollEndNotification`, so once per scroll gesture, with the final offset.

**Choices to check**
- The doc doesn't say how often the "started", "changed" and "scrolled" events should fire. I chose once per field, once per drag and once per gesture. Easy to change if product wants different granularity.
- If the user unticks and re-ticks the terms box, `terms_accepted` fires again.

I couldn't confirm the code compiles or runs: I didn't run `flutter analyze` or the app, and `dart format` printed nothing I could check.
