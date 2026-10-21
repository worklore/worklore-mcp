# Analytics events

Implemented all six events from `docs/EVENTS.md` via `Analytics.capture`, with names and properties unchanged. I fired them in places that avoid one event per keystroke or slider step.

- `registration_email_started` / `registration_phone_started`: fire on the first `onChanged` per screen visit, behind `_emailInputFired` / `_phoneInputFired` flags. No email or phone values are sent.
- `loan_amount_changed` (`amount`): fires from the slider's `onChangeEnd`, once per drag. `onChanged` only updates the UI.
- `terms_accepted`: fires only when the checkbox changes to ticked.
- `registration_continue_tapped` (`amount`, `terms`): fires when Continue is tapped, before navigating.
- `offers_scrolled` (`offset`): `OfferScreen` is now a `StatefulWidget`. It listens for `ScrollEndNotification` and fires once per visit, with the offset at the first scroll end. Say so if you want one event per scroll end instead.

Not run: I haven't run `flutter analyze` or a build, and I haven't checked a debug build with `PostHogConfig.debug`. `dart format` may not have been available either.
