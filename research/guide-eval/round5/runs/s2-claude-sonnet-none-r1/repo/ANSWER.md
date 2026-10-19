# Ticket #4471 – empty replays on the new UI

**Cause:** posthog_flutter session replay works by screenshotting the widget
tree under a `PostHogWidget`. `LegacyApp` wraps its `MaterialApp` in
`PostHogWidget`; `NewApp` (go_router, `MaterialApp.router`) never did. Events and
screen tracking still work (they come from `Analytics.init()` and
`PosthogObserver`), which is why only the recording is missing. Project
settings and SDK version are not involved.

**Fix:** `lib/new_app.dart` now wraps the app content in `PostHogWidget` via
`MaterialApp.router(builder: ...)`, so it sits above the router's Navigator.

**Not verified:** I couldn't run Flutter/PostHog here. Check on a device that a
new-UI session shows up in Replay. Past sessions on the new UI are not
recoverable. Also note `maskAllTexts = true` is set, so text will appear masked
in recordings (by design).
