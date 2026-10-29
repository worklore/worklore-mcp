# Analytics events implemented

Added all six events from `docs/EVENTS.md` through `Analytics.capture`.

- `registration_email_started` and `registration_phone_started` fire on the first nonempty edit, once per registration screen instance. Neither field value is sent.
- `loan_amount_changed` fires when the slider interaction ends, with the chosen `amount` as an `int`.
- `terms_accepted` fires when the checkbox is ticked.
- `registration_continue_tapped` fires on an enabled Continue tap, with `amount` as an `int` and `terms` as a `bool`.
- `offers_scrolled` fires when the offers list stops scrolling, with its pixel `offset` as a `double`.

The colleague's note applied to the text fields, slider, and scroll list: the first-edit flags avoid a capture per keystroke, and the slider and scroll events use end callbacks instead of update callbacks. Its advice to preserve event names and properties and omit sensitive field values also applied. Focus listeners and final-value capture did not apply because the event spec asks for typing starts and no field values. No PostHog debug session was run; the configured project key is a CI placeholder.

Verification: `flutter analyze` completed with no issues, and `git diff --check` passed.
