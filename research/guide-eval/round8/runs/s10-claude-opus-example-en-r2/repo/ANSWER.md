# Analytics events: registration and offers screens

All six events in `docs/EVENTS.md` now go through `Analytics.capture` (`lib/analytics.dart`).
Event names and properties match the spec exactly.

| Event | Where | When it fires |
|---|---|---|
| `registration_email_started` | `registration_screen.dart`, email `TextField.onChanged` | On the first keystroke only, once per screen visit (`_emailStartedSent` flag) |
| `registration_phone_started` | `registration_screen.dart`, phone `TextField.onChanged` | On the first keystroke only, once per screen visit (`_phoneStartedSent` flag) |
| `loan_amount_changed` `{amount: int}` | `Slider.onChangeEnd` | Once per drag or tap, when the user lets go, with the final rounded amount |
| `terms_accepted` | `CheckboxListTile.onChanged` | Only when the box becomes ticked. Unticking sends nothing |
| `registration_continue_tapped` `{amount: int, terms: bool}` | Continue button `onPressed` | On each tap, before navigating to `/offers` |
| `offers_scrolled` `{offset: double}` | `offer_screen.dart`, `NotificationListener<ScrollEndNotification>` around the list | Once per scroll gesture, when it stops. `offset` is `metrics.pixels`. Only the list's own scrolls count (`depth == 0`) |

The email and phone number are never sent (PII rule in the spec). No screen-view
events were added, because `PosthogObserver` already tracks them.

Checks: `dart format` and `flutter analyze` both pass with no issues. I did not run
the app on a device or emulator, so I have not watched the events arrive in a
debug log. `flutter analyze` ran `pub get` and edited `analysis_options.yaml` on
its own; I undid both, so the only changed files are the two screens and this one.

## Colleague's note: which parts applied

The README says the app is on the PostHog free tier, and the spec's wording
("started typing", "moved the slider", "scrolled") points straight at
per-change callbacks. So the note's main warning applied directly. If I had
hooked these events into `onChanged` or scroll updates, the dashboards would
have looked right while the event quota ran out.

**Applied:**
- Text fields: a once-per-visit flag in `onChanged` (step 2). The spec asks
  for "started", not the final value, so firing on the first edit is the
  correct meaning, not just a cheaper one.
- Slider: the capture is in `onChangeEnd`, and `onChanged` only updates the UI (step 5).
- Scroll: `ScrollEndNotification`, not scroll updates or a `ScrollController`
  listener (step 6).
- Event names and properties kept exactly as specified (step 7).

**Did not apply / ignored:**
- The audit of existing captures (the "Check if this applies" grep). The
  screens sent no events yet, so there was nothing to fix. I built it right
  from the start instead.
- `FocusNode` tap/focus events and focus-lost capture (steps 3–4). No event in
  the spec is about focus or needs a field's final value.
- The "per visit vs per flow" question. `_RegistrationScreenState` lives on the
  root route and stays alive under `/offers`. So if a user goes back from
  offers and edits again, they won't send a second `*_started` event. That fits
  a funnel. Re-opening the screen creates a new state and resets the flags.
- The verification steps that use PostHog (`PostHogConfig.debug`, PostHog →
  Activity). I did not run the app or contact any external service.

## Open questions for product
- `terms_accepted` and `registration_continue_tapped` fire on every tick or
  tap. These are single discrete actions, so the volume is small. If the funnel
  should count each user only once, add a flag like the text-field ones.
- `offers_scrolled` fires once per scroll gesture. That is a handful per visit,
  not hundreds. If only "did they scroll at all" matters, a once-per-visit flag
  would cut it to one event.
- On a tall screen, all 10 offers may fit without scrolling. Those users would
  never send `offers_scrolled` and would look like drop-offs in the funnel.
