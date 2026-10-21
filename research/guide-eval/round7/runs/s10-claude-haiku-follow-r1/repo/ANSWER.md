# Analytics events on the registration and offers screens

Implemented the six events in `docs/EVENTS.md`, all sent through the existing
`Analytics.capture` wrapper in `lib/analytics.dart`. Event names and property
keys match the spec exactly. No PII is sent.

## What changed

**`lib/screens/registration_screen.dart`**

| Event | Where it fires | Notes |
|---|---|---|
| `registration_email_started` | Email field `onChanged`, first edit only | Guarded by `_emailStartedFired` so it fires once per screen state, not per keystroke. |
| `registration_phone_started` | Phone field `onChanged`, first edit only | Same pattern with `_phoneStartedFired`. |
| `loan_amount_changed` | Slider `onChangeEnd` | Property `amount` = `v.round()`. Fires once per drag. `onChanged` still only updates the UI. |
| `terms_accepted` | Checkbox `onChanged` when the value becomes `true` | Unticking does not fire. |
| `registration_continue_tapped` | Continue button, via new `_onContinue()` | Properties `amount` (int) and `terms` (bool), captured before navigating to `/offers`. |

**`lib/screens/offer_screen.dart`**

| Event | Where it fires | Notes |
|---|---|---|
| `offers_scrolled` | `NotificationListener<ScrollEndNotification>` wrapping the `ListView` | Property `offset` = `notification.metrics.pixels` (double). Returns `false` so scroll notifications keep propagating. |

## Decisions

- **"Started" events are once per screen visit.** `EVENTS.md` says "started
  typing", and the README says events should not flood the per-event-billed
  quota. The flags live on the registration screen's state. That route stays
  on the stack while `/offers` is open, so the flags also persist across a
  back-navigation. In practice that means once per app session on that
  screen, not once per return.
- **`terms_accepted` fires only on tick, not untick.** The spec says "ticked".
  A user who ticks, unticks, and re-ticks will send two events. That is a
  discrete action, not a per-change stream, so I did not add a once-only flag.
- **`loan_amount_changed` uses `onChangeEnd`.** This follows the per-drag
  rule. A tap without a drag also ends the change and fires once. Its
  `amount` is the final value.

## Verification

- `flutter analyze`: no issues.
- `dart format --set-exit-if-changed lib`: no changes needed.
- Not run on a device or emulator. I did not run a debug build with
  `PostHogConfig.debug = true`, so the per-keystroke and per-drag reductions
  are verified by reading the code, not by watching a log. Nothing was sent to
  PostHog.
- `flutter pub get` was needed for analysis. It also rewrote
  `analysis_options.yaml` and created `.dart_tool/` and `pubspec.lock`. I
  reverted the config and removed the generated files, so the diff contains
  only the two screens and this file.

## Not done

- No commit made.
- `docs/EVENTS.md` unchanged.
- The `phc_REPLACE_ME_IN_CI` placeholder key in `lib/analytics.dart` is still
  in place. Events will not reach PostHog until CI injects the real key.
