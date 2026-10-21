# Registration and offers analytics events

Implemented the six events in `docs/EVENTS.md` on the registration and offers
screens, using the existing `Analytics.capture` wrapper. Names and properties
match the spec exactly. Nothing is committed.

## What changed

**`lib/screens/registration_screen.dart`**

| Event | Where it fires | Properties |
|---|---|---|
| `registration_email_started` | Email `onChanged`, first edit only (`_emailStartedFired` flag) | — |
| `registration_phone_started` | Phone `onChanged`, first edit only (`_phoneStartedFired` flag) | — |
| `loan_amount_changed` | Slider `onChangeEnd` (once per drag, not per step) | `amount` (int) |
| `terms_accepted` | Checkbox `onChanged`, when value becomes `true` | — |
| `registration_continue_tapped` | Continue button `onPressed`, before navigating | `amount` (int), `terms` (bool) |

**`lib/screens/offer_screen.dart`**

| Event | Where it fires | Properties |
|---|---|---|
| `offers_scrolled` | `NotificationListener<ScrollEndNotification>` wrapping the list (once per scroll gesture) | `offset` (double, `metrics.pixels` at the end of the scroll) |

No email or phone values are sent (PII rule in the spec).

The flags live on the `RegistrationScreen` state. That state is recreated each
time the route is pushed, so "once" means once per screen visit, which is what
the spec asks for.

## Colleague's note: what applied

- **Text fields fire once per visit, not per keystroke.** Applied. The two
  "started typing" events use a once-only flag in `onChanged`.
- **Slider moves to `onChangeEnd`.** Applied to `loan_amount_changed`.
  `onChanged` still only updates the UI.
- **Scroll uses `ScrollEndNotification`, not per-update.** Applied to
  `offers_scrolled`.
- **Keep event names and properties unchanged.** Applied; all names and
  properties come straight from `docs/EVENTS.md`.
- **Focus-lost / final-value events.** Not applicable. No event in the spec
  needs the field's final value, so none is sent on focus loss.
- **Tap/focus once-only pattern.** Not applicable. The terms checkbox is handled
  through its value, and Continue is a single tap.
- **"Which events may stay per-change."** None. The spec doesn't allow any
  per-change event, so none was kept.
- **Dashboard and PostHog verification steps.** Not done. I had no device or
  PostHog access.

The note's background (the PostHog quota incident) is not something I could
check here, and it does not change the code.

## Verification

- `flutter analyze`: no issues.
- `dart format --set-exit-if-changed lib`: no changes needed.
- Not run on a device, and events were not checked in PostHog.

`flutter pub get` changed `analysis_options.yaml` and created `pubspec.lock`
and `.dart_tool/`. I reverted those and removed the generated files, so the
diff contains only the three source edits plus this file.

## Behaviour to review

1. **`loan_amount_changed` fires on a tap without a move.** Flutter calls
   `onChangeEnd` on a plain tap as well. The spec says "moved", so a guard
   against an unchanged value would be stricter. I did not add one.
2. **`terms_accepted` fires on every tick.** Ticking, unticking and ticking
   again sends two events. I kept it simple because the spec says "ticked".
   A once-per-visit flag would change that if product wants one event per
   visit.
3. **`offers_scrolled` reports the end position only.** `offset` is the
   pixel position when the scroll stops, not the distance travelled. It also
   fires for any scroll that ends, including programmatic ones.
4. **Capture calls are not awaited.** This matches the existing wrapper's
   fire-and-forget use. Errors from `Posthog().capture` will not surface at
   the call site.
