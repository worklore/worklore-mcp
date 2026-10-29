# Analytics events: registration funnel

I added all six events from `docs/EVENTS.md`. Every event goes through
`Analytics.capture` (`lib/analytics.dart`), and the event names match the spec
exactly.

## Where each event fires

| Event | Code | When it fires |
|---|---|---|
| `registration_email_started` | `registration_screen.dart`, `_onEmailChanged` | On the first non-empty input in the email field, **once per screen visit** |
| `registration_phone_started` | `registration_screen.dart`, `_onPhoneChanged` | On the first non-empty input in the phone field, **once per screen visit** |
| `loan_amount_changed` `{amount: int}` | `registration_screen.dart`, `Slider.onChangeEnd` | Once when a drag or tap on the slider ends, with the final rounded amount |
| `terms_accepted` | `registration_screen.dart`, `_onTermsChanged` | Only when the checkbox goes from unticked to ticked. Unticking sends nothing |
| `registration_continue_tapped` `{amount: int, terms: bool}` | `registration_screen.dart`, `_onContinue` | Right before navigating to `/offers` |
| `offers_scrolled` `{offset: double}` | `offer_screen.dart`, `NotificationListener<ScrollEndNotification>` | Once when a scroll gesture settles, with `metrics.pixels` (only for the list itself, `depth == 0`) |

## Choices I made

- **Volume (free tier).** A simple version would hook `onChanged` everywhere.
  That sends an event on every keystroke, every slider frame and every scroll
  frame, which would use up the PostHog free-tier quota quickly and inflate the
  funnel. Instead:
  - the "started" events are de-duplicated with a flag,
  - the slider uses `onChangeEnd`,
  - scrolling uses `ScrollEndNotification`.

  This works out to about one event per user action.
- **PII.** No email or phone value is sent. The text fields only check whether
  the value is non-empty.
- **`terms` on continue.** The Continue button is only enabled when terms are
  accepted, so `terms` will always be `true` in practice. I still send it
  because the spec asks for it.
- **Repeat events.** `loan_amount_changed`, `terms_accepted` and
  `offers_scrolled` can fire more than once per visit if the user repeats the
  action. That is intended: each one is a real interaction. Funnels should count
  unique users rather than total events.
- I didn't add any screen-view events, since `PosthogObserver` already tracks
  those.

## Verification

- `dart format` and `flutter analyze` passed with no issues.
- I didn't run the app or any tests (the repo has none), and I sent no events
  anywhere.
- `flutter pub get` created `pubspec.lock` and `.dart_tool/`, and
  `flutter analyze` rewrote `analysis_options.yaml`. I reverted all three, so
  the only changed files are the two screens and this file.

## Worth flagging (not changed)

- `Analytics.init` runs in every build, including debug. Once the real key is
  added in CI, local and dev runs will also send events to the production
  project and use up the free-tier quota. You could disable capture in
  `kDebugMode`, or use a separate project key for dev.
