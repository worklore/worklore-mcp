# PostHog Session Replay Issue Analysis & Fix

## 1. Why Session Replay Was Empty on the New UI

In Flutter, PostHog mobile session replay generates video replays by capturing snapshots/screenshots of the widget tree. This mechanism requires the root app widget (`MaterialApp` / `MaterialApp.router` / `CupertinoApp`) to be wrapped in a `PostHogWidget`.

- In `lib/legacy_app.dart`, `MaterialApp` was correctly wrapped inside `PostHogWidget(child: MaterialApp(...))`.
- In `lib/new_app.dart`, `MaterialApp.router` was returned directly without a `PostHogWidget` wrapper.

Because `PostHogWidget` was missing in `NewApp`:
- The PostHog SDK still successfully initialized and recorded lifecycle events, screen views (via `PosthogObserver`), and custom tap/action events.
- However, without `PostHogWidget`, no UI frame snapshots were captured or sent to PostHog.
- Consequently, sessions from the new UI had empty recordings in the Replay tab despite event timelines appearing normally.

---

## 2. What Was Fixed

Wrapped `MaterialApp.router` in `lib/new_app.dart` with `PostHogWidget`:

```dart
    // PostHogWidget is required to capture screenshots of the widget tree
    // for mobile session replay. Without it, events are recorded but replays are empty.
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

## 3. Which Parts of the Colleague's Note Applied

### Applied:
- **Core Diagnosis & Root Cause:** Mobile Flutter replay relies on `PostHogWidget` wrapping the root app widget to capture screenshot frames. Missing this wrapper results in events being tracked normally while replay remains completely empty without errors.
- **Multiple App Shell Scenario:** The specific pitfall where an older app shell (`legacy_app.dart`) had the wrapper, but a newly introduced redesign shell (`new_app.dart`) missed the wrapper.
- **Verification Steps Check:**
  - `pubspec.yaml` contains `posthog_flutter` (version `^5.36.0`).
  - `lib/analytics.dart` configures `sessionReplay = true` during `Posthog().setup(config)`.
  - `observers: [PosthogObserver()]` was already present in `_router` in `lib/new_app.dart`.
- **Fix Pattern:** Wrapping `MaterialApp.router` in `PostHogWidget` and adding an explanatory comment to prevent future regressions.

### Did Not Apply / Ignored:
- **`startSessionRecording()` behind feature flags:** The app does not gate recording dynamically with `startSessionRecording()`; it enables replay directly via `config.sessionReplay = true` in `lib/analytics.dart`.
- **Trial-and-error console setting adjustments / store release iteration:** Not applicable to the direct codebase diagnosis and fix.
- **`CupertinoApp` checks:** The project uses Material (`MaterialApp` and `MaterialApp.router`).
