# Analytics events implementation

All six events from `docs/EVENTS.md` are implemented on the two screens, sent
through the existing `Analytics.capture` wrapper (`lib/analytics.dart`). Event
names and properties match the spec exactly; no PII (email/phone values) is
sent anywhere.

## Registration screen (`lib/screens/registration_screen.dart`)

| Event | Where it fires | Properties |
|---|---|---|
| `registration_email_started` | First edit of the email field per visit of the screen (`onChanged`, guarded by `_emailStartedFired`) | — |
| `registration_phone_started` | First edit of the phone field per visit (`onChanged`, guarded by `_phoneStartedFired`) | — |
| `loan_amount_changed` | `Slider.onChangeEnd` — once per drag, when the user lets go | `amount` (int, `v.round()`) |
| `terms_accepted` | Checkbox `onChanged`, only when the box becomes ticked (`v == true`), not on untick | — |
| `registration_continue_tapped` | Continue button `onPressed` (button is only enabled when `_canContinue`, so it always fires from a valid state), before navigating to `/offers` | `amount` (int), `terms` (bool) |

The once-per-visit flags live on the screen `State`, so they reset when the
screen is popped and recreated — "once" means once per visit, matching the
funnel semantics.

## Offers screen (`lib/screens/offer_screen.dart`)

`offers_scrolled` fires from a `NotificationListener<ScrollEndNotification>`
wrapped around the `ListView.builder` — once per scroll gesture, at the end,
with `offset` (double, `notification.metrics.pixels`). The screen stays
stateless; the listener needs no state.

## Colleague's note — what applied

This codebase is exactly the case the note describes (Flutter + PostHog, free
tier billed per event, events hooked to `onChanged`/slider callbacks), and the
fix pattern applied directly:

- **"Text fields: fire once per screen visit, on the first edit"** — applied
  verbatim: `_emailStartedFired` / `_phoneStartedFired` flags in the screen
  state, capture only `if (!fired)`, then set the flag. Without this, each
  field would emit one event per keystroke (~20 per email).
- **"Sliders: move the event from `onChanged` to `onChangeEnd`"** — applied:
  `onChanged` only updates the UI, the capture is in `onChangeEnd`, so one drag
  = one event with the chosen amount.
- **"Scrolls: listen for `ScrollEndNotification` rather than every scroll
  update"** — applied: `offers_scrolled` fires per scroll end, not per scroll
  frame.
- **"Keep event names and properties unchanged"** — applied: names and
  properties are exactly as in `docs/EVENTS.md`, so existing dashboards and
  funnels keep working.

Parts of the note I deliberately did not use:

- **FocusNode-based "final value" capture** — not needed: no event requires a
  field's final value, and the spec forbids sending the email/phone values as
  properties, so there is nothing to capture on focus loss.
- **Untick behavior for the checkbox** — the note doesn't cover checkboxes; I
  fire `terms_accepted` only on tick (an untick is not an acceptance), which
  matches the spec's "User ticked the terms and conditions checkbox".
- **The debugging steps (PostHog debug build verification)** — could not be
  run here (no device/emulator; sending events to PostHog was out of scope
  anyway per the note's own ground rules). Verified statically instead (below).

## Verification

- `dart format` applied to both changed files.
- `flutter analyze` (Flutter 3.47.9 stable): **No issues found!**
  Note: the Flutter/Dart toolchains installed on this machine under the user's
  home directory could not be executed from this shell (macOS TCC "Operation
  not permitted"), so a standalone Flutter SDK was downloaded to `/tmp` to run
  `pub get` and `analyze`, then deleted. Runtime verification on a
  device/emulator was not possible here; the once-only firing behavior follows
  the pattern verified in the colleague's note (one event per field visit, one
  per slider drag, one per scroll gesture).
