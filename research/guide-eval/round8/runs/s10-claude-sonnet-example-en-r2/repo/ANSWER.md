# Analytics events

Implemented all six events from `docs/EVENTS.md` through `Analytics.capture`, with the exact names and properties. No email or phone values are sent.

Registration screen:
- `registration_email_started` / `registration_phone_started`: fire on the first edit only, behind `_emailStartedFired` / `_phoneStartedFired` flags. `onChanged` runs on every keystroke.
- `loan_amount_changed` (`amount`): sent from the slider's `onChangeEnd`, so once per drag.
- `terms_accepted`: sent only when the box is ticked, not when it is unticked.
- `registration_continue_tapped` (`amount`, `terms`): sent on the Continue tap.

Offers screen:
- `offers_scrolled` (`offset`): sent from a `NotificationListener<ScrollEndNotification>`, so once per scroll gesture.

## Colleague's note
Applied: the per-event billing and free-tier concern matches our README. Following the note, I avoided firing on every keystroke, slider step or scroll update, using a once-per-visit flag, `onChangeEnd` and `ScrollEndNotification`.
Not applied: the focus-lost handling (no event needs a final value) and the `PostHogConfig.debug` verification. I didn't run the app.

Caveats: the start flags live in the screen state, so they reset if the screen is rebuilt. `offers_scrolled` can still fire several times per visit, once per gesture. Say so if product wants it limited to the first scroll. I only ran `dart format`, not the analyzer or tests.
