# Analytics events: registration and offers screens

All six events from `docs/EVENTS.md` are now sent through `Analytics.capture`.
Event names and properties match the spec exactly. Email and phone values are
never sent (PII).

We're on the PostHog free tier, which is billed per event. The naive approach
(capture in `onChanged`) would send one event per keystroke and one per slider
step while dragging, and that would use up the quota quickly. So each event is
attached to a callback that fires once per user action.

| Event | Where | When it fires |
|---|---|---|
| `registration_email_started` | `registration_screen.dart`, email `onChanged` | Once, on the first edit. `_emailStartedFired` stops it repeating on later keystrokes. |
| `registration_phone_started` | same, phone `onChanged` | Once, on the first edit (`_phoneStartedFired`). |
| `loan_amount_changed` `{amount: int}` | Slider `onChangeEnd` | Once per drag or tap, when the user lets go, with the final rounded amount. `onChanged` still only updates the UI. |
| `terms_accepted` | Checkbox `onChanged` | Only when the box goes from unticked to ticked. Unticking sends nothing. |
| `registration_continue_tapped` `{amount: int, terms: bool}` | Continue button `onPressed` | On each tap, just before navigating to `/offers`. |
| `offers_scrolled` `{offset: double}` | `offer_screen.dart`, `NotificationListener<ScrollEndNotification>` around the list | Once per scroll gesture, when it settles. `offset` is `metrics.pixels`. Only the list's own scroll counts (`depth == 0`). Per-frame scroll updates are ignored. |

## Decisions to check
- **What "once" means for the "started" events.** The flags live on the
  registration screen's state. That state stays alive while the user is on
  `/offers` and comes back, so the "started" events fire once per registration
  flow, not again after going back. They fire again only if the screen is
  rebuilt from scratch, e.g. after an app restart.
- **`terms_accepted` and `offers_scrolled` can repeat.** If someone ticks the
  box, unticks it and ticks it again, you get two `terms_accepted`. Each
  separate scroll gesture sends its own `offers_scrolled`. Both are discrete
  user actions, so the volume stays low. If the funnel should count each only
  once per visit, adding a flag is a one-line change.
- **No scroll, no event.** If all 10 offers fit on the screen (large tablets),
  the list can't scroll and `offers_scrolled` never fires. That would show up
  as funnel drop-off.

## Verification
- `flutter analyze` reports no issues.
- I did not run the app on a device. To check manually: set
  `config.debug = true` in `Analytics.init`, then
  - type a full email: the log shows one `registration_email_started`
  - drag the slider end to end: one `loan_amount_changed` when you let go
  - fling the offers list: one `offers_scrolled` per fling

Files changed: `lib/screens/registration_screen.dart`, `lib/screens/offer_screen.dart`.
`lib/analytics.dart` is unchanged.
