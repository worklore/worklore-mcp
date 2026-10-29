# Analytics events implemented

The registration screen now sends `registration_email_started` and
`registration_phone_started` on the first nonempty edit of each field per
screen visit. It sends `loan_amount_changed` when a slider interaction that
changed the amount ends, with the chosen integer `amount`. Checking the terms
box sends `terms_accepted`. An enabled Continue tap sends
`registration_continue_tapped` with the integer `amount` and boolean `terms`
before opening offers.

The offers screen sends `offers_scrolled` once per screen visit, after the
first completed scroll with a positive offset. The `offset` property is a
double measured from the top of the list. All six events use the existing
`Analytics.capture` wrapper. No email or phone value is sent.

The colleague's note applied to the input, slider, and scroll events: text
events are guarded against per-keystroke captures, the slider event uses
`onChangeEnd`, and the scroll event uses `ScrollEndNotification`. The suggested
focus listeners and final-value capture did not apply because these events
do not need final text values or tap/focus tracking. The PostHog debug and
dashboard checks were not run; they require a configured external service.

Verification: `flutter analyze` completed with no issues.
