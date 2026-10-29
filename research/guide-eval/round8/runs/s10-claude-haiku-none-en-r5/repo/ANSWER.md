# Registration and offers analytics

Implemented the six events from `docs/EVENTS.md` on the registration and offers
screens. All sends go through `Analytics.capture`. No other files were changed
beyond `lib/screens/registration_screen.dart` and `lib/screens/offer_screen.dart`.

## What was added

| Event | Where | Behaviour |
|---|---|---|
| `registration_email_started` | `registration_screen.dart` | Sent once per screen visit, on the first character typed in Email. |
| `registration_phone_started` | `registration_screen.dart` | Sent once per screen visit, on the first character typed in Phone. |
| `loan_amount_changed` | `registration_screen.dart` | `amount` (int). Sent when the slider drag ends (`onChangeEnd`), not on every step. |
| `terms_accepted` | `registration_screen.dart` | Sent only when the checkbox is ticked, not when it is unticked. |
| `registration_continue_tapped` | `registration_screen.dart` | `amount` (int) and `terms` (bool). Sent before navigating to `/offers`. |
| `offers_scrolled` | `offer_screen.dart` | `offset` (double, `metrics.pixels`). Sent once per finished scroll (`ScrollEndNotification`). |

## Decisions I made where the spec was open

- **One-shot typing events.** `registration_email_started` and
  `registration_phone_started` fire on the first non-empty `onChanged`, so they
  are not repeated on every keystroke. The flags reset only when the screen is
  recreated.
- **Slider sends the final value.** `onChanged` fires on every drag step, which
  would flood a free-tier PostHog project. I used `onChangeEnd`, so
  `amount` is the value the user settled on. If product wants every intermediate
  step, change this one callback.
- **Scroll sends once per gesture.** Scroll notifications fire every frame, so
  `offers_scrolled` uses `ScrollEndNotification`. `offset` is the position at the
  end of the scroll.
- **PII.** Email and phone values are never sent. The start events carry no
  properties at all.
- **`terms` in continue.** The Continue button is disabled unless `_terms` is
  true, so `terms` is always `true` in practice. It is still sent as the spec asks.

## Verification

- `dart format --set-exit-if-changed lib/screens` passes after formatting.
- `flutter analyze` reports "No issues found" on the code before the final
  comment-wrapping and formatting pass. That pass changed only whitespace and
  comments.
- Not run: the app on a device or simulator, and a check that events arrive in
  PostHog. The PostHog key in `lib/analytics.dart` is still the placeholder
  `phc_REPLACE_ME_IN_CI`, so nothing was sent anywhere during this work.

## Side effects of running the analyzer (reverted)

`flutter analyze` ran a package resolve. It created `pubspec.lock` and
`.dart_tool/`, and rewrote `analysis_options.yaml` to exclude platform
directories. I reverted `analysis_options.yaml` with `git checkout` and removed
the two generated paths. `pubspec.yaml` was not changed. The working tree now
contains only the two screen files plus this `ANSWER.md`.

## Not done

- `docs/EVENTS.md` status line ("waiting for implementation") was left as is,
  since updating it is a product decision.
- Nothing was committed, pushed, or sent to any external service.
