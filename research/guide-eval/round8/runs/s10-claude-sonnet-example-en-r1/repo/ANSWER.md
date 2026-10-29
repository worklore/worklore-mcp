# Analytics events

Implemented all six events from `docs/EVENTS.md` using `Analytics.capture`, with the exact names and properties. No email or phone values are sent.

- `registration_email_started` / `registration_phone_started`: fire in `onChanged`, but only on the first edit per screen visit (`_emailStartedFired`, `_phoneStartedFired`).
- `loan_amount_changed`: fires from the slider's `onChangeEnd`, once per drag, with `amount`. `onChanged` only updates the UI.
- `terms_accepted`: fires when the box is ticked (not when unticked).
- `registration_continue_tapped`: fires when Continue is tapped, with `amount` and `terms`, before navigating.
- `offers_scrolled`: fires from a `NotificationListener<ScrollEndNotification>` (top-level list only), with `offset` = scroll pixels. It fires once per completed scroll, not per scroll update. A user who scrolls many times sends many events. If that is too many, add a once-per-visit flag.

## Colleague's note
Applied: the per-keystroke / per-slider-step / per-scroll-update quota problem, which is the same hazard here (the spec's events map onto `onChanged` and scroll). I used the once-per-visit flag, `onChangeEnd` and `ScrollEndNotification` fixes. Not applied: the focus-lost variant (no event needs the final value), `FocusNode` tap events, and the debug-log verification (not run; no Flutter build was done here). Nothing was compiled or run.
