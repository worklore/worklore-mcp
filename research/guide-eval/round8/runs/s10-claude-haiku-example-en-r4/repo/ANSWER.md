# Analytics events: registration and offers screens

Implemented the six events in `docs/EVENTS.md`, all sent through `Analytics.capture`
(`lib/analytics.dart`). Event names and property names match the spec exactly.
No PII is sent: email and phone values are never included.

## What changed

**`lib/screens/registration_screen.dart`**

| Event | Trigger | Properties |
|---|---|---|
| `registration_email_started` | First edit of the email field in a screen visit | none |
| `registration_phone_started` | First edit of the phone field in a screen visit | none |
| `loan_amount_changed` | Slider drag ends (`onChangeEnd`) | `amount` (int) |
| `terms_accepted` | Checkbox ticked (`onChanged` with `true`) | none |
| `registration_continue_tapped` | Continue pressed (only when enabled) | `amount` (int), `terms` (bool) |

- Email and phone have `bool` flags (`_emailStartedFired`, `_phoneStartedFired`) on the
  screen state. `RegistrationScreen` is a fresh route each time it opens, so the flags
  reset per visit. The first edit fires the event; later keystrokes do not.
- The slider's `onChanged` still updates the UI only. The event moved to `onChangeEnd`,
  so one drag produces one event with the final amount.

**`lib/screens/offer_screen.dart`**

| Event | Trigger | Properties |
|---|---|---|
| `offers_scrolled` | `ScrollEndNotification` on the offers list | `offset` (double, `metrics.pixels`) |

- Wrapped the `ListView` in a `NotificationListener<ScrollEndNotification>`. It fires once
  per scroll gesture, not per scroll update. It returns `false` so the notification keeps
  bubbling.

## Which parts of the colleague's note applied

The note describes a Flutter app with the same per-keystroke and per-slider-step problem,
so its fixes were relevant here.

- **Applied: text fields fire once per visit on the first edit.** This matches the spec's
  wording ("started typing"). The flag is on the screen state, and each visit creates a new
  state, so "once" means "once per visit". There is only one screen in this flow, so per
  visit and per flow are the same.
- **Applied: sliders move the event to `onChangeEnd`.** `loan_amount_changed` is "moved the
  slider", so one event per drag is what the spec describes. The event name was kept, as
  the note advised.
- **Applied: scroll events use `ScrollEndNotification`.** Not `ScrollUpdateNotification` or a
  controller listener.
- **Applied: keep event and property names unchanged.** Dashboards depend on them.
- **Not applicable: focus-lost events for final values.** No event in the spec needs the
  field's final value, and email and phone are not sent.
- **Not applicable: tap/focus `FocusNode` guards.** The spec has no focus events. Terms and
  Continue are single actions, so they need no once-only guard.
- **Not applicable: "which events may stay per-change".** The spec gives none that should
  stay per-change, so I treated every event as once per action.
- **Not done: the debug-build verification.** I did not run the app or check PostHog's
  activity log. I have no device or PostHog access here, and the ground rules forbid sending
  anything to an external service.

## Judgment calls

- `terms_accepted` fires each time the box is ticked, not when it is unticked. The spec says
  "ticked".
- `registration_continue_tapped` fires only when the button is enabled, since a disabled
  button can't be tapped. It fires before navigation.
- `loan_amount_changed` also fires on a plain tap on the slider, because `onChangeEnd` runs
  then too. That still counts as one change.
- `Analytics.capture` is not awaited, consistent with how the wrapper is written.

## Verification

- `dart format` applied to `lib/` (one line wrapped in `registration_screen.dart`).
- `flutter analyze` on the final code: **No issues found.**
- `git status` shows only the two screen files modified. `flutter analyze` also rewrote
  `analysis_options.yaml` and created `pubspec.lock` and `.dart_tool/`. I reverted the config
  file and deleted the generated files, so none of that is in the diff.
- Not run: the app on a device, or any check that events reach PostHog.

## Open issue

`lib/analytics.dart` still has the placeholder key `phc_REPLACE_ME_IN_CI`. Events won't reach
PostHog until CI supplies the real key. This was already the case before my change and I
didn't touch it.

## Not committed

Changes are in the working tree only. Nothing was committed or pushed.
