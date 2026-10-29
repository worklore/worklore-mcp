# Analytics events on the registration and offers screens

Implemented the six events in `docs/EVENTS.md`, using the existing
`Analytics.capture` wrapper. Names and properties match the spec exactly.

## What changed

### `lib/screens/registration_screen.dart`

| Event | Where it fires | Notes |
|---|---|---|
| `registration_email_started` | Email `TextField.onChanged` | Once per screen visit (flag `_emailStartedSent`). |
| `registration_phone_started` | Phone `TextField.onChanged` | Once per screen visit (flag `_phoneStartedSent`). |
| `loan_amount_changed` | Slider `onChangeEnd`, `{amount: v.round()}` | Once per drag, with the final amount. `onChanged` still only updates the UI. |
| `terms_accepted` | Checkbox `onChanged`, only when ticked | Once per screen visit (flag `_termsAcceptedSent`). Untick and re-tick send nothing new. |
| `registration_continue_tapped` | Continue button `onPressed`, before navigating | `{amount: _amount.round(), terms: _terms}`. |

No email or phone values are sent anywhere.

### `lib/screens/offer_screen.dart`

| Event | Where it fires | Notes |
|---|---|---|
| `offers_scrolled` | `NotificationListener<ScrollEndNotification>` wrapping the `ListView` | `{offset: metrics.pixels}` (double). Fires once when a scroll settles. The listener returns `false` so the notification keeps bubbling. |

## Choices I made where the spec was open

- **Text fields and terms fire once per visit.** The spec says "started typing" and "ticked", so I read these as the first occurrence. Firing on every keystroke would produce about 20 events per email address.
- **Slider fires on `onChangeEnd`, not `onChanged`.** The spec says "moved the slider", and `onChanged` fires on every step during a drag. `onChangeEnd` gives one event per drag with the final amount. This changes when the event fires, not its name or properties.
- **Scroll fires on `ScrollEndNotification`.** Same reasoning as the slider. The spec doesn't say whether it should be per gesture or per update; I chose per gesture.
- **Continue is only tracked when enabled.** The button is disabled until the form is valid, so a disabled tap sends nothing. If product wants disabled taps counted, that needs a separate event.
- **Once per visit means per `RegistrationScreen` state.** Returning to `/` creates a new state, so the flags reset.

## Colleague note: what applied

Applied:
- Text-field events behind a once-only flag. The spec's "started" events matched this directly.
- Slider capture moved from `onChanged` to `onChangeEnd`, with `onChanged` kept for UI only.
- Scroll capture from `ScrollEndNotification`, not from scroll updates.
- Event names and properties kept as the spec defines them, so dashboards keep working.

Did not apply:
- The `FocusNode` / focus-lost pattern for "final value" events. No event in the spec needs a text field's final value, and the spec forbids sending the email or phone as properties.
- Tap/focus-listener guards. Not needed; the spec has no focus or tap events on these screens.
- Checking the PostHog dashboard and debug logs. I couldn't reach PostHog from here, so the checks below ran against a mocked channel instead (see Verification).
- The colleague's grep for existing `onChanged` captures. I read the three source files directly instead; there were no existing capture calls in the repo before this change.

## Verification

- `dart format` passes on `lib/` (after formatting, one line was wrapped).
- `flutter analyze`: no issues.
- I wrote a temporary widget test that mocks the `posthog_flutter` method channel and drives both screens. It confirmed:
  - Typing 2+ characters into email and phone sends one `*_started` event each.
  - One slider drag sends exactly one `loan_amount_changed` with an `int` amount that differs from the start value.
  - Ticking, unticking, and re-ticking terms sends one `terms_accepted`.
  - Continue sends one `registration_continue_tapped` with `amount` (int) and `terms: true`, then navigates to Offers.
  - One scroll on Offers sends one `offers_scrolled` with a positive double `offset`.
  - All four tests passed.
- I deleted that test afterwards, since it wasn't part of the request. Nothing was deployed, published, or sent to PostHog.
- `flutter pub get` and `flutter test` modified `analysis_options.yaml` and created `pubspec.lock`, `.dart_tool/` and `build/`. I reverted and removed all of them, so the only changes are the two screen files and this file.

Not verified: that events reach the real PostHog project and show up in the dashboards. That needs a debug build with `PostHogConfig.debug = true` against the real key (currently `phc_REPLACE_ME_IN_CI`, which CI supplies).

## Follow-ups (not done)

- `README.md` says "the screens do not send any of them yet". That is now out of date.
- The PostHog key in `lib/analytics.dart` is still a placeholder that CI replaces.
