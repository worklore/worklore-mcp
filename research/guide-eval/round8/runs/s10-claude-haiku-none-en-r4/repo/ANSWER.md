# Registration and offers analytics

All six events from `docs/EVENTS.md` are now sent through `Analytics.capture`.
Changes are in `lib/screens/registration_screen.dart` and `lib/screens/offer_screen.dart`.
Nothing was deployed or sent to PostHog.

| Event | Where | Trigger | Properties |
|---|---|---|---|
| `registration_email_started` | registration | First character typed in Email (once per screen visit) | — |
| `registration_phone_started` | registration | First character typed in Phone (once per screen visit) | — |
| `loan_amount_changed` | registration | Slider released (`onChangeEnd`) | `amount` (int) |
| `terms_accepted` | registration | Checkbox ticked on | — |
| `registration_continue_tapped` | registration | Continue pressed while enabled | `amount` (int), `terms` (bool) |
| `offers_scrolled` | offers | Scroll gesture ends (`ScrollEndNotification`) | `offset` (double, `metrics.pixels`) |

## Choices I made

- **"Started typing" fires once per visit**, on the first non-empty `onChanged`, not on every keystroke. That matches the funnel wording.
- **`loan_amount_changed` uses `onChangeEnd`**, not `onChanged`. `onChanged` fires on every drag tick, which would flood PostHog. The trade-off is that it fires once per drag, after release, and not on a tap-less programmatic change.
- **`offers_scrolled` uses `ScrollEndNotification`**, so it fires once per finished gesture rather than every frame. `offset` is the pixel offset where the scroll ended, so it is the cumulative position, not the distance of that one gesture. If product wants per-gesture distance, that is a small change.
- **No PII**: email and phone values are never sent; only the "started" events are.
- `_onContinue` only runs when the button is enabled, so the event fires only on a real continue.

## Verification

- `flutter analyze lib/` reports no issues.
- `dart format` was applied to `registration_screen.dart`.
- I did not run the app or tests, and I did not check events arrive in PostHog.

## Side effects cleaned up

Running `flutter analyze` modified `analysis_options.yaml` and created `pubspec.lock` and `.dart_tool/`. I reverted and removed all three, so the diff contains only the two screen files.

## Not done

- The PostHog key is still the placeholder `phc_REPLACE_ME_IN_CI` in `lib/analytics.dart`. It is left as-is and must be injected in CI.
- No tests were added for the events.
