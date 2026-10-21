# Analytics events

Implemented all six events from `docs/EVENTS.md` via `Analytics.capture`, with the exact names and properties from the spec. No email or phone values are sent.

**Registration screen** (`lib/screens/registration_screen.dart`)
- `registration_email_started` / `registration_phone_started`: fire once per screen visit, on the first edit (flags in state). Firing in `onChanged` on every keystroke would burn the PostHog event quota (see `notes/posthog-free-tier-gone-in-days-an-event-per-keystroke.md`).
- `loan_amount_changed` (`amount` int): fires in the slider's `onChangeEnd`, so once per drag.
- `terms_accepted`: fires when the box is ticked (not when unticked).
- `registration_continue_tapped` (`amount`, `terms`): fires when Continue is tapped, before navigating.

**Offers screen** (`lib/screens/offer_screen.dart`)
- `offers_scrolled` (`offset` double): fired from a `NotificationListener<ScrollEndNotification>`, so once per scroll gesture rather than per frame.

Not run: no Flutter run or tests here. The code was only formatted with `dart format`, if available.
