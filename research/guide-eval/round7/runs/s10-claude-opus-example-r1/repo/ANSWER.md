# Analytics events: registration and offers screens

All six events from `docs/EVENTS.md` now fire. They go through `Analytics.capture`, and the names and property types match the spec exactly. I didn't touch the wrapper (`lib/analytics.dart`) or `main.dart`.

| Event | Where | When it fires |
|---|---|---|
| `registration_email_started` | `registration_screen.dart`, email `TextField.onChanged` | **Once** per screen state, on the first edit (`_emailStartedSent` flag) |
| `registration_phone_started` | phone `TextField.onChanged` | **Once** per screen state, on the first edit (`_phoneStartedSent` flag) |
| `loan_amount_changed` `{amount: int}` | `Slider.onChangeEnd` | Once per drag or tap, when the user lets go. It's skipped if the value ends where it started |
| `terms_accepted` | `CheckboxListTile.onChanged` | Only when the box is ticked, not when it's unticked |
| `registration_continue_tapped` `{amount: int, terms: bool}` | Continue button `onPressed` | On each tap, just before the screen goes to `/offers` |
| `offers_scrolled` `{offset: double}` | `offer_screen.dart`, `NotificationListener<ScrollEndNotification>` | Once per scroll gesture, when the scroll stops. Only for the list itself (`depth == 0`), and only if the offset differs from the last one sent |

The email and phone values are never sent as properties, so no PII goes out. `OfferScreen` became a `StatefulWidget` so it can remember the last offset it sent.

## What I used from the colleague's note

The README says we're on the PostHog free tier, so the note's main warning applies here. If I had wired the spec's wording ("started typing", "moved the slider", "scrolled") straight into `onChanged` or scroll updates, we'd send one event per keystroke, per slider step and per scroll frame.

**Parts that applied:**
- **Text fields:** send once per visit on the first edit, using a `bool` flag in the screen state. The event names already say "started", so once is what the spec means anyway.
- **Slider:** send from `onChangeEnd` and keep `onChanged` for updating the UI only.
- **Scroll:** send from `ScrollEndNotification`, never from scroll updates or a `ScrollController` listener.
- **Event names and properties:** kept exactly as the spec has them, since dashboards are already built on them.

**Parts I didn't use:**
- **The focus-node approach** (tap or focus events, and sending the final value when focus is lost). No event here needs either.
- **The PostHog troubleshooting and "verify in PostHog → Activity" steps.** There was no existing code to fix, and I didn't connect to any external service.

**What I added beyond the note:**
- `loan_amount_changed` is skipped when a drag ends on the same value it started from.
- `offers_scrolled` is skipped when the offset hasn't changed, for example after an overscroll bounce.
- `terms_accepted` fires only on ticking.

## Decisions you may want to revisit
- **Meaning of "once" for the started events.** `RegistrationScreen` is the root route, so its state survives the push to `/offers` and the trip back. In practice, "once" means once per app session until the screen is rebuilt, not once per visit. That seems right for a funnel. If you want it per visit, reset the flags when the user comes back to the screen.
- **`offers_scrolled` fires once per scroll gesture, not once per visit.** Each event carries the offset where that gesture stopped. If you only need "did they scroll" plus the furthest point, a single event per visit would use even less quota.
- **`registration_continue_tapped` fires on every tap.** That's one event per real user action, so it's cheap.

## Checks
- `dart format lib`: done.
- `flutter analyze`: no issues.
- No tests: the repo has none, and I didn't run the app on a device. To check it, run a debug build with `PostHogConfig.debug = true`. Typing a full email should log one `registration_email_started`, and one slider drag should log one `loan_amount_changed`.
- Running `flutter pub get`/`analyze` added an `analyzer.exclude` block to `analysis_options.yaml` and created `.dart_tool/` and `pubspec.lock`. I reverted the yaml change and deleted the two generated items, so the diff only touches the two screen files.
