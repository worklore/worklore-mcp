# Analytics events from docs/EVENTS.md

All six events are now sent through `Analytics.capture` (`lib/analytics.dart`).
Event names and properties match the spec exactly. Email and phone values are
never sent.

| Event | Where | When it fires |
|---|---|---|
| `registration_email_started` | `registration_screen.dart`, email `onChanged` | Once per screen visit, on the first edit (`_emailStartedFired` flag) |
| `registration_phone_started` | `registration_screen.dart`, phone `onChanged` | Once per screen visit, on the first edit (`_phoneStartedFired` flag) |
| `loan_amount_changed` `{amount: int}` | Slider `onChangeEnd` | Once per drag or tap, when the user lets go. `onChanged` still only updates the UI |
| `terms_accepted` | Checkbox `onChanged` | Only when the box goes from unticked to ticked, never on untick |
| `registration_continue_tapped` `{amount: int, terms: bool}` | Continue button `onPressed` | Each tap, before navigating to `/offers` |
| `offers_scrolled` `{offset: double}` | `NotificationListener<ScrollEndNotification>` around the offers `ListView` | Once per scroll gesture, after any fling settles. `offset` = `metrics.pixels`. `depth == 0` so only the list's own scroll counts |

Checks: `dart format` and `flutter analyze` (with `flutter_lints`) report no
issues. I did not run the app on a device or emulator, and there are no
widget tests in the repo, so the firing counts in the table haven't been tested at
runtime. Running `flutter analyze` made the Flutter tool rewrite
`analysis_options.yaml` and create `.dart_tool/` and `pubspec.lock`. I
reverted or deleted all of those, so only the two screen files changed.

## Which parts of the colleague's note applied

The situation matches the note: a Flutter app, PostHog, and per-event billing
on the free tier (README). The spec wording ("started typing", "moved the
slider", "scrolled") would lead straight into the bug if you put the capture
in `onChanged` or scroll updates. These parts applied:

- **Text fields: once-per-visit flag on the screen state.** Used as written
  for both `*_started` events. "Once" means per visit: the flags live on
  `_RegistrationScreenState`, which stays alive while `/offers` is pushed on
  top. So going back and editing again does not re-fire, but reopening the
  screen does. The spec's event means "started typing", so firing on the first
  keystroke matches it.
- **Sliders: `onChangeEnd` instead of `onChanged`.** Used as written.
- **Scrolls: `ScrollEndNotification`, not updates or a controller listener.**
  Used as written. It also gives a sensible "how far they scrolled" value.
- **Keep names and properties unchanged.** Followed. They match EVENTS.md
  exactly.

These parts did not apply:

- **The `FocusNode` focus/tap handler and the "fire on focus lost to get the
  final value" step.** No event needs a field's final value, and the spec has
  no tap or focus events for the fields.
- **The PostHog `debug = true` / Activity verification.** I didn't run the
  app, and I didn't touch `Analytics.init`. That check is still worth doing
  on a debug build: type a full email and you should see one capture, and a
  drag across the slider should give one event.

## Decisions you may want to revisit

- `offers_scrolled` fires once per scroll gesture, not once per visit. That's
  enough for the funnel and costs about one event per flick. If the
  free-tier budget is tight, an option is to send a single event with the
  maximum offset when the user leaves the screen. Also note that on tall
  screens the 10-offer list may not scroll at all, so this step of the funnel
  can never happen for those users.
- `terms_accepted` fires again if the user unticks and re-ticks. That's rare
  and cheap. A once-per-visit flag would remove it if needed.
