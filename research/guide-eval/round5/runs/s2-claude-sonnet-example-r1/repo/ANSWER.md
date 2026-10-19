# Ticket #4471 – no replays on the new UI

**Cause:** `lib/new_app.dart` (`NewApp`, `MaterialApp.router`) was not wrapped in `PostHogWidget`; `lib/legacy_app.dart` was. On mobile, Flutter replay is built from screenshots taken by `PostHogWidget`. Without it, events, screens and taps still arrive (the observer is present) but no frames are sent, so the Replay tab is empty. No error is logged. This matches the ticket: same build, same SDK, same project settings; only the A/B group on the legacy shell is recorded.

**Fix:** wrapped `MaterialApp.router` in `PostHogWidget` in `lib/new_app.dart`, with a comment explaining why.

**Checked, fine:** `analytics.dart` sets `sessionReplay = true`; `PosthogObserver` is on the GoRouter.

**Colleague's note:** applied: the missing wrapper diagnosis, the "check every MaterialApp" advice, and the explanatory comment. Not applicable: the `startSessionRecording()` flag gating (we use `sessionReplay = true`), and the PII masking step (`maskAllTexts` is already set).

**Not verified:** I did not build or run the app (no device); confirm on a real device that a new-UI session shows up in Replay. Note `maskAllTexts = true` means text will be masked in replays by design.
