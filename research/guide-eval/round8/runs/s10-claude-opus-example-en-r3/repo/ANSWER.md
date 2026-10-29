# Analytics events: what was done

All six events from `docs/EVENTS.md` now go through `Analytics.capture`
(`lib/analytics.dart`). Event names and properties match the spec exactly, and
no email or phone value is sent.

| Event | Where | When it fires |
|---|---|---|
| `registration_email_started` | `registration_screen.dart`, email `onChanged` | On the first edit only. Guarded by `_emailStartedFired` |
| `registration_phone_started` | `registration_screen.dart`, phone `onChanged` | On the first edit only. Guarded by `_phoneStartedFired` |
| `loan_amount_changed` `{amount: int}` | Slider `onChangeEnd` | Once per drag or tap, when the user lets go. `onChanged` still only updates the UI |
| `terms_accepted` | Checkbox `onChanged` | Only when the box becomes ticked, not when it is unticked |
| `registration_continue_tapped` `{amount: int, terms: bool}` | Continue button `onPressed` | Once per tap, before navigating to `/offers` |
| `offers_scrolled` `{offset: double}` | `NotificationListener<ScrollEndNotification>` around the offers `ListView` | Once per scroll gesture, when scrolling stops. `offset` is `metrics.pixels`. Only the list's own notifications count (`depth == 0`) |

Check: `flutter analyze` reports no issues. I did not run the app or write
widget tests, so the event counts have not been checked on a device.

## Which parts of the colleague's note applied

The note fits this project: it is Flutter, it uses PostHog, and the README says
we are on the free tier. Read literally, the spec wording ("started typing",
"moved the slider", "scrolled") leads to the per-keystroke and per-frame
pattern the note warns about.

Applied:
- **Text fields:** a once-only `bool` flag in `onChanged`.
- **Slider:** capture in `onChangeEnd`, not `onChanged`.
- **Scroll:** capture on `ScrollEndNotification`, not on scroll updates or a
  `ScrollController` listener.
- **Names and properties:** kept exactly as the spec defines them.

Not applied:
- **FocusNode tap/focus events:** the spec has no such events.
- **Final value on focus lost:** no event needs the field's value, and the
  values are PII anyway.
- **Verification steps:** I did not run `PostHogConfig.debug` or look at the
  PostHog dashboard. I don't deploy or send anything to external services.

## Notes / open points
- **"Once per visit":** the flags live in the registration `State`. Pushing
  `/offers` keeps that State alive, so going Back and typing again does not
  re-fire the "started" events. The flags reset only when the screen is
  rebuilt from scratch (e.g. app restart). For a funnel that seems right; tell
  me if product wants "per visit" instead.
- **`terms_accepted` repeats:** it fires each time the box is ticked again
  after being unticked. That is bounded by real taps, so the cost is small.
  Ask product if it should be once only.
- **`offers_scrolled` volume:** this is per scroll gesture, not once per visit.
  If product only needs "did they scroll", a once-per-visit flag would cut the
  volume further.
- **`analysis_options.yaml`:** it changed on disk while I was working (an
  `analyzer.exclude` block was added). I did not make that change and left it
  as is.
