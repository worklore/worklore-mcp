# Analytics implementation

Implemented all events from `docs/EVENTS.md` through the existing `Analytics.capture` wrapper.

- `registration_email_started` and `registration_phone_started`: sent on the first edit to each field, guarded by separate once-per-screen-visit flags. No email address or phone number is sent.
- `loan_amount_changed`: sent from the slider's `onChangeEnd`, with the chosen amount rounded to an `int` in the `amount` property. UI updates remain in `onChanged`.
- `terms_accepted`: sent only when the checkbox changes to checked.
- `registration_continue_tapped`: sent before navigating to Offers, with `amount` as an `int` and `terms` as a `bool`.
- `offers_scrolled`: sent from `NotificationListener<ScrollEndNotification>`, with the final scroll position in pixels as the double `offset` property.

No screen-view events were added because those are already automatic.

## Colleague's note

Applied:
- Once-per-screen-visit flags for text-field input events, avoiding one event per keystroke.
- `onChangeEnd` for the slider, avoiding one event per slider step.
- `ScrollEndNotification` for scrolling, avoiding an event for every scroll update.
- The specified event names and properties were kept unchanged.

Not applicable:
- Focus/tap capture and focus-lost handling for final field values: the specification has no focus events or final-value properties, and email/phone values must not be collected.
- The note's PostHog dashboard/debug-network reproduction steps were not used; no analytics data was sent to an external service.

## Verification

- `git diff --check` passed.
- Audited the capture sites against all six rows in `docs/EVENTS.md`; text, slider, and scroll captures use the quota-safe triggers above.
- Flutter formatting, static analysis, and runtime/widget checks could not be run because macOS denied access to the installed Flutter/Dart launchers and tool snapshots (`Operation not permitted`). The project has no existing test suite.
