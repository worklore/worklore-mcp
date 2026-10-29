# Analytics events on the registration and offers screens

All six events in `docs/EVENTS.md` are now sent through `Analytics.capture`.
Event names and property names are unchanged. Changes are in
`lib/screens/registration_screen.dart` and `lib/screens/offer_screen.dart`.
Nothing is committed.

## What each event does

| Event | Where it fires | Properties |
|---|---|---|
| `registration_email_started` | Email `onChanged`, once per screen state, guarded by `_emailStarted` | none |
| `registration_phone_started` | Phone `onChanged`, once per screen state, guarded by `_phoneStarted` | none |
| `loan_amount_changed` | Slider `onChangeEnd` (once per drag, not per step) | `amount` (int, rounded) |
| `terms_accepted` | Checkbox `onChanged`, only when ticked on | none |
| `registration_continue_tapped` | Continue `onPressed`, before navigating to `/offers` | `amount` (int, rounded), `terms` (bool) |
| `offers_scrolled` | `NotificationListener<ScrollEndNotification>` around the offers `ListView` | `offset` (double, `metrics.pixels`) |

No email or phone values are sent as properties.

## Colleague's note: what applied

The note describes a PostHog quota problem caused by capturing inside
`onChanged` on every keystroke and every slider step. This repo has not
shipped those captures yet, so the fix is applied up front. Parts that applied:

- **Text fields → once per visit with a flag.** Applied to the email and phone
  "started" events. The flags live on the screen state.
- **Slider → `onChangeEnd`.** Applied to `loan_amount_changed`. The spec says
  "moved", so one event per drag fits.
- **Scroll → `ScrollEndNotification`, not `ScrollUpdateNotification` or a
  controller listener.** Applied to `offers_scrolled`.

Parts that did not apply:

- **Focus-lost events for final values.** No spec event needs the final text
  value, so there is no focus listener.
- **Tap/focus `FocusNode` guards.** No spec event is a focus or tap event, apart
  from the checkbox, which is handled by its own `onChanged`.
- **Debug build and PostHog dashboard check.** I did not run a debug build
  against PostHog or check the Activity view. That would send events to an
  external service, which the ground rules rule out. I used a mock channel
  instead (below).
- **The quota story and model/date metadata.** Context only, not applicable.

## Decisions you may want to check

1. **"Once per visit" means once per `RegistrationScreen` state.** The screen
   stays on the navigator stack when the user goes to `/offers`. If they come
   back and edit the fields, the "started" events do not fire again.
2. **`offset` is the scroll position where scrolling stopped.** The spec says
   "how far they scrolled", which could also mean the distance moved in that
   gesture. I used `metrics.pixels` because the name is "offset". Tell me if
   product wants the distance instead.
3. **`loan_amount_changed` also fires on a tap without a drag.** That is how
   `Slider.onChangeEnd` behaves. I think that is acceptable.
4. **`terms` in `registration_continue_tapped` is always `true`.** The button is
   only enabled when terms are accepted. The property is still sent, as the spec
   asks.
5. **`offers_scrolled` may fire on a gesture that does not move the list** (for
   example, a drag at the top edge). I did not test this.

## Verification

- `flutter analyze`: no issues.
- `dart format --set-exit-if-changed lib/`: clean.
- Temporary widget tests with a mocked `posthog_flutter` channel: all 4 passed.
  - Email and phone "started" each fired once across several `enterText` calls.
  - One slider drag produced exactly one `loan_amount_changed` with a valid amount.
  - Terms fired on tick but not on untick, and again on the next tick.
  - Continue sent `{amount: 50000, terms: true}` and navigated to Offers.
  - One offers scroll produced one `offers_scrolled` with a positive double offset.

  I deleted the test file afterwards so the change stays within the requested
  scope. It can be added to the repo if you want it kept.

## Environment side effects, cleaned up

`flutter pub get` changed `analysis_options.yaml` (it added analyzer excludes).
I reverted that file. I also removed the generated `.dart_tool/`, `pubspec.lock`
and `build/` directories. The only remaining changes are the two screen files
and this `ANSWER.md`.

## Still open

- `lib/analytics.dart` still has the placeholder key `phc_REPLACE_ME_IN_CI`.
  The events will go nowhere until CI injects the real key. This was already the
  case before my change and I did not touch it.
