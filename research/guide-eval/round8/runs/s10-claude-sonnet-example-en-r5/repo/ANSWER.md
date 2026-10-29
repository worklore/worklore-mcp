# Analytics events implementation

Implemented all six events from `docs/EVENTS.md` using `Analytics.capture`. Names and properties match the spec. No email or phone values are sent.

- `registration_email_started` / `registration_phone_started`: fire in `onChanged` behind a per-screen-state `bool` flag, so once per visit and not once per keystroke.
- `loan_amount_changed` (`amount`): fires from the Slider's `onChangeEnd`, so once per drag. `onChanged` only updates the UI.
- `terms_accepted`: fires when the checkbox is ticked (not when unticked).
- `registration_continue_tapped` (`amount`, `terms`): fires in the Continue button handler before navigation.
- `offers_scrolled` (`offset`): fires from `NotificationListener<ScrollEndNotification>`, so once per scroll gesture, not on every scroll update.

## Colleague's note
Applied: the whole approach. The spec's "started typing" and "moved the slider" events sit naturally in `onChanged`, which would have sent one event per keystroke or slider step and burned the quota. I used the once-per-visit flags, `onChangeEnd` and `ScrollEndNotification` as the note describes. Not needed: the focus-lost variant, because no event carries a final field value.

Not verified: I didn't run the app or `flutter analyze` (no Flutter run was done). `offers_scrolled` can still fire several times per visit, once per gesture. If that is too many, add a once-per-visit flag.
