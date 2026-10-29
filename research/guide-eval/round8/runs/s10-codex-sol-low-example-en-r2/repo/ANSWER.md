# Analytics events implemented

Added all six events from `docs/EVENTS.md` through the existing `Analytics.capture` wrapper:

- Registration email and phone start events fire on the first nonempty edit per screen visit. Neither sends entered text.
- `loan_amount_changed` fires when a slider interaction ends, with the chosen amount as an `int`.
- `terms_accepted` fires when the checkbox changes from unchecked to checked.
- `registration_continue_tapped` fires on an enabled Continue tap, with integer `amount` and boolean `terms`.
- `offers_scrolled` fires after a scroll ends, with the final offset as a `double`. It only fires when the list moved.

The colleague's note applied to limiting text input events to once per screen visit, recording slider changes at `onChangeEnd`, and recording scrolling at scroll end. Its focus handling, final field value capture, PostHog debug build, and dashboard checks did not apply here. Event names and properties match the approved spec; no email or phone value is captured.

Verification: `flutter analyze` completed with no issues, and `git diff --check` passed. Runtime PostHog event counts were not checked.
