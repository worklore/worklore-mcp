# Analytics events implementation

All six events from docs/EVENTS.md are implemented through `Analytics.capture`, with names and properties unchanged.

- `registration_email_started` and `registration_phone_started` fire from `onChanged` on the first edit only. A `_emailStartedFired` or `_phoneStartedFired` flag on the screen state stops repeats. No email or phone value is sent.
- `loan_amount_changed` (`amount` as an int) fires from the slider's `onChangeEnd`, so once per drag. `onChanged` only updates the UI.
- `terms_accepted` fires when the checkbox changes to ticked. Unticking sends nothing.
- `registration_continue_tapped` (`amount`, `terms`) fires on the Continue tap, before navigation.
- `offers_scrolled` (`offset` as `metrics.pixels`) fires from a `NotificationListener<ScrollEndNotification>`, so once per finished scroll rather than per scroll update.

## Colleague's note
- **Applied:** the once-per-visit flags for the text fields, `onChangeEnd` for the slider and `ScrollEndNotification` for scrolling. The spec's wording ("started typing", "moved the slider", "scrolled") would otherwise have led to per-keystroke and per-step events and a quickly exhausted quota.
- **Not applicable:** focus-lost capture, because no event needs a field's final value. I made no changes to the PostHog config or debug settings.

## Not verified
I didn't build or run the app, and I didn't run `flutter analyze`.

The flags are per screen-state instance. If the screen is rebuilt, they reset.
