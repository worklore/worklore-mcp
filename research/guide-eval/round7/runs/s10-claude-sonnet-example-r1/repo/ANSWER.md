# Analytics events implementation

Implemented all six events from `docs/EVENTS.md` via `Analytics.capture`, keeping names and properties exactly as specced. No PII is sent.

- `registration_email_started` / `registration_phone_started`: fired from `onChanged`, guarded by a per-screen-state flag, so once per visit (not per keystroke).
- `loan_amount_changed` (`amount`): fired from the slider's `onChangeEnd`, once per drag. `onChanged` only updates UI.
- `terms_accepted`: on checkbox tick (not on untick). Discrete tap, no throttling needed.
- `registration_continue_tapped` (`amount`, `terms`): in the Continue button handler before navigation.
- `offers_scrolled` (`offset`): `OfferScreen` became stateful; fired from `NotificationListener<ScrollEndNotification>`, once per visit, with the offset when the first scroll settled.

## Colleague's note
Applied: the whole per-event-quota idea. The spec's "started typing", "moved the slider" and "scrolled" events map naturally to per-keystroke / per-step / per-scroll-update callbacks, which would burn quota. I used once-per-visit flags for text fields, `onChangeEnd` for the slider and `ScrollEndNotification` for scrolling.
Not applied: focus-loss capture and FocusNodes (no event needs a final value); the PostHog debug-log verification (not run).

## Notes
- Not compiled or run: Flutter SDK was not used here, so please run `flutter analyze` and a debug build.
- Judgment call: `offers_scrolled` is once per visit and `terms_accepted` fires only on tick; adjust if the funnel wants otherwise.
