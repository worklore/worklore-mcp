# Analytics events implemented

- Registration captures `registration_email_started` and `registration_phone_started` once on the first edit of each field per screen visit. Neither field value is sent.
- The amount slider captures `loan_amount_changed` on drag completion with an integer `amount`. Checking the terms captures `terms_accepted` on each transition to checked. Tapping Continue captures `registration_continue_tapped` with integer `amount` and boolean `terms`.
- Offers captures `offers_scrolled` on the first completed scroll per screen visit with a double `offset`.
- All events use the existing `Analytics.capture` wrapper. No screen view event was added.

The colleague's note applied to first-edit text events, slider capture on `onChangeEnd`, and scroll capture on `ScrollEndNotification` to avoid sending an event for every update. Its focus handling and final field value advice did not apply because these events need no field values. PostHog debug mode and Activity verification were not used; those require running the app and checking the external service.

Verification: `flutter analyze` passed with no issues. Runtime event counts were not verified.
