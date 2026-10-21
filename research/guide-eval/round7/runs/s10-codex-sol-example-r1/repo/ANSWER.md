# Analytics events implemented

- Registration sends `registration_email_started` and `registration_phone_started` once per screen visit, on the first edit of each field. Neither event includes the entered value.
- The slider sends `loan_amount_changed` with the selected integer `amount` when the user finishes moving it. The terms checkbox sends `terms_accepted` when it changes to checked. Continue sends `registration_continue_tapped` with integer `amount` and boolean `terms` before opening offers.
- The offers list sends `offers_scrolled` with a double `offset` when scrolling ends.
- All six events use the existing `Analytics.capture` wrapper. Automatic screen view tracking was left as configured.

## Colleague note

The advice about event volume applies: the registration fields use `onChanged`, so their events are guarded to fire once per screen visit; the slider event uses `onChangeEnd`; the offers event uses `ScrollEndNotification`. There were no analytics captures in those callbacks before this change, so the reported per-keystroke quota problem was not present here. Focus listeners and final field values do not apply to the approved event spec.

## Verification

`flutter analyze --no-pub` passed after resolving the dependencies. `dart format --output=none --set-exit-if-changed` found no formatting changes, and `git diff --check` passed. No PostHog Activity or device session was available for a live event count check.
