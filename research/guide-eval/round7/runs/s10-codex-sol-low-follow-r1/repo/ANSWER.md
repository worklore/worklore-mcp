# Analytics events implemented

Added all six events from `docs/EVENTS.md` through `Analytics.capture`.

- Registration email and phone started events fire on the first edit of each field per screen visit. Neither field's value is sent.
- Loan amount changed fires at the end of a slider drag with the selected amount as an `int`.
- Terms accepted fires when the checkbox becomes checked.
- Registration continue tapped fires when the enabled button is tapped, with the current amount (`int`) and terms state (`bool`).
- Offers scrolled fires when a scroll ends at a positive offset, with the offset as a `double`.

`flutter analyze` passed with no issues. A live PostHog capture check was not run because the app uses a placeholder project key.
