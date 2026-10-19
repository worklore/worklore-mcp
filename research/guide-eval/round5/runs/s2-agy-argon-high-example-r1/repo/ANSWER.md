# Why Session Replay Was Empty on the New UI

## Root Cause

On Flutter mobile (`posthog_flutter`), session replay is built from screenshots of the widget tree captured by `PostHogWidget`. If a root `MaterialApp` / `MaterialApp.router` is not wrapped in `PostHogWidget`, the SDK still initializes normally, sends custom events (`loan_amount_changed`, `application_submitted`, taps, lifecycle events), and tracks screen transitions via `PosthogObserver()`, without logging any error or warning—but it has no frames to capture or upload, resulting in empty/missing session recordings.

This app ships two root shells selected in `lib/main.dart`:
- **Old UI (`LegacyApp` in `lib/legacy_app.dart`):** Wrapped its `MaterialApp` in `PostHogWidget`, so session replay worked for the A/B group (`NEW_UI=false`).
- **New UI (`NewApp` in `lib/new_app.dart`):** Returned `MaterialApp.router(...)` directly without wrapping it in `PostHogWidget`, so users on the redesigned UI (`NEW_UI=true`) sent events and screen views but produced no session replay frames.

## Fix

In `lib/new_app.dart`, wrapped `MaterialApp.router` in `PostHogWidget` inside `NewApp.build()` and added a comment explaining that `PostHogWidget` is required for PostHog session replay to capture frames:

```dart
// PostHogWidget is required for PostHog session replay to capture frames.
return PostHogWidget(
  child: MaterialApp.router(
    title: 'Loanly',
    theme: ThemeData(
      colorSchemeSeed: Colors.indigo,
      useMaterial3: true,
    ),
    routerConfig: _router,
  ),
);
```

---

## Which Parts of the Colleague's Note Applied

### Applied
- **Core explanation and second-shell pitfall:** The exact scenario described in the note applied—a redesigned UI shell using `MaterialApp.router` (`lib/new_app.dart`) was added alongside the legacy `MaterialApp` shell (`lib/legacy_app.dart`), and `PostHogWidget` was omitted from the new shell while events, taps, and screen tracking continued to work silently.
- **"Check if this applies to you" (Checks 1–3):**
  1. `pubspec.yaml` depends on `posthog_flutter: ^5.36.0` (satisfying `>= 5.14.0`).
  2. `lib/analytics.dart` enables replay (`config.sessionReplay = true`).
  3. Comparing `MaterialApp` / `MaterialApp.router` and `PostHogWidget` across `lib/` immediately pinpointed that `lib/legacy_app.dart` had `PostHogWidget` while `lib/new_app.dart` did not.
- **Steps 1 & 2 (Locate all root app widgets, wrap the missing `MaterialApp.router` in `PostHogWidget`, and add a comment):** Applied directly to `NewApp.build()` in `lib/new_app.dart`.

### Ignored / Already in Place
- **Importing `package:posthog_flutter/posthog_flutter.dart` (part of Step 2):** Already imported at the top of `lib/new_app.dart` for `PosthogObserver()`.
- **Step 3 (Enabling `config.sessionReplay = true` or calling `startSessionRecording()`):** `config.sessionReplay = true` was already configured before `Posthog().setup(config)` in `lib/analytics.dart`, and feature-flag gating via `startSessionRecording()` is not used in this codebase.
- **Step 4 (Adding `PosthogObserver()` to navigation/router observers):** Already present in both `lib/legacy_app.dart` (`navigatorObservers: [PosthogObserver()]`) and `lib/new_app.dart` (`observers: [PosthogObserver()]` on `_router`).
- **Step 5 (Setting `config.sessionReplayConfig.maskAllTexts = true`):** Already set in `lib/analytics.dart`.
- **PostHog project settings checks (sampling, retention, enabling "Record user sessions"):** Already confirmed working and enabled (100% sampling, minimum duration 0) per `SUPPORT-TICKET.md` since the legacy UI was recording properly in the same project and build.
- **Live device/emulator verification against PostHog ("Verify" section):** Not applicable in this local repository (`lib/analytics.dart` uses placeholder key `phc_REPLACE_ME_IN_CI`, and external network/service reporting is out of scope per ground rules).
