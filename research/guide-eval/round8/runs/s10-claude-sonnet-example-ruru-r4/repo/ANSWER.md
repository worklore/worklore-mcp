# Analytics events implemented

All six events from `docs/EVENTS.md` are sent through `Analytics.capture`. Names and properties match the spec. No PII is sent.

## Registration (`lib/screens/registration_screen.dart`)
- `registration_email_started` and `registration_phone_started`: sent from `onChanged`, but only once per screen visit, guarded by the `_emailStartedFired` / `_phoneStartedFired` flags.
- `loan_amount_changed` (`amount`): sent from the slider's `onChangeEnd`, so once per drag. `onChanged` only updates the UI.
- `terms_accepted`: sent when the checkbox becomes ticked. Unticking sends nothing.
- `registration_continue_tapped` (`amount`, `terms`): sent when the Continue button is tapped, before navigation.

## Offers (`lib/screens/offer_screen.dart`)
- `offers_scrolled` (`offset`): `OfferScreen` is now a `StatefulWidget`. A `NotificationListener<ScrollEndNotification>` sends the event once per visit, the first time a scroll ends with `pixels > 0`. `offset` is the scroll position at that moment.

## Which parts of the colleague's note were useful
- Used: the warning that `onChanged` fires on every keystroke and every slider step, which would burn the free-tier quota. That is why the text fields use a once-per-visit flag, the slider uses `onChangeEnd`, and scrolling uses `ScrollEndNotification` rather than update notifications.
- Used: keeping event names and properties unchanged.
- Skipped: the `FocusNode` / blur-based capture. No event needs the final field value, and the spec forbids sending email or phone anyway.
- Skipped: the PostHog debug build check. I did not run the app, and I did not send anything externally.

## Notes
- `offers_scrolled` fires once per visit rather than per scroll gesture. That is enough for the funnel and cheapest on quota. If product wants one per gesture, remove the `_scrolledFired` flag.
- I did not run `flutter analyze` or the app. Check that the edited files compile.
