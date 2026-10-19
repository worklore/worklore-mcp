# Ticket #4471: why new-UI users have no replays

**Cause:** `NewApp` (`lib/new_app.dart`) returned a bare `MaterialApp.router`. On mobile,
posthog_flutter builds replays from screenshots of the widget tree, and `PostHogWidget`
is what takes them. `LegacyApp` wraps its `MaterialApp` in it; the redesign didn't.
Without the wrapper the SDK still sends events (screens, taps, custom events), but has
no frames, so no replay appears, and there's no error or warning. That matches the ticket.

**Ruled out:** Project settings (recording on, 100% sampling, min duration 0), SDK
version (same build), and the config in `lib/analytics.dart` (`sessionReplay = true`,
set before setup, shared by both shells). `PosthogObserver` is already on the GoRouter.

**Fix:** wrapped `MaterialApp.router` in `PostHogWidget` in `lib/new_app.dart`, with a
comment saying why. These are the only two root app widgets in `lib/`.

**Not verified:** I didn't run the app (no Flutter run or device here). To check: run
the new UI on a device, visit 3–4 screens, background the app, and confirm the session
plays back screens in PostHog. Sessions from before the release can't be recovered.
Any future third shell (flavor, white-label) needs the same wrapper.
