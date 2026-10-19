# Session replay on the new UI

The redesigned shell in `lib/new_app.dart` returned `MaterialApp.router` without a `PostHogWidget`. PostHog still received events through the shared SDK and `PosthogObserver`, but the replay SDK had no widget frames to capture. The legacy shell already had the wrapper, which explains why only its sessions appeared.

Wrapped the new shell's `MaterialApp.router` in `PostHogWidget` and added a comment explaining its replay role. The shared configuration already enables `sessionReplay` before `Posthog().setup(config)`, and the new router already has `PosthogObserver()`.

Verification: `flutter analyze` passed with no issues. A replay was not verified in PostHog: this checkout has no iOS or Android project files to run on the available simulator, and the configured project key is a CI placeholder. After the next mobile build, navigate through several screens, background the app to flush, and confirm the session has visible frames in PostHog Session replay.
