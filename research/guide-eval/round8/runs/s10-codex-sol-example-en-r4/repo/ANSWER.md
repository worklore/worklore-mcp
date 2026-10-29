# Analytics events implemented

The registration screen now sends `registration_email_started` and
`registration_phone_started` on the first edit of each field per screen
instance. It sends `loan_amount_changed` with the selected integer `amount`
when a slider interaction ends, `terms_accepted` when the checkbox changes to
accepted, and `registration_continue_tapped` with integer `amount` and boolean
`terms` when Continue is tapped. The offers screen sends `offers_scrolled` with
the final double pixel `offset` when scrolling ends at a new position. All six
events use the existing `Analytics.capture` wrapper. No email or phone value is
sent.

The colleague's note applied to the text fields, slider, and scrolling: first
edit flags prevent an event per keystroke, `onChangeEnd` prevents an event per
slider step, and `ScrollEndNotification` prevents an event per scroll update.
Its focus listeners and final field value advice did not apply because the
spec requests first typing events with no field properties. Its PostHog debug
and Activity checks were not used; no live analytics service was contacted.

Verification: `dart analyze` completed with no issues, and `git diff --check`
passed.
