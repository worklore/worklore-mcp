# PostHog Session Replay Issue Analysis & Fix

## 1. Why Session Replay Was Empty on the New UI

In Flutter, PostHog's mobile session replay captures wireframe/screenshot images of the widget tree using the `PostHogWidget` wrapper widget. Without wrapping the root application widget (`MaterialApp` / `MaterialApp.router` / `CupertinoApp`) in `PostHogWidget`:
- Standard events, screen views, and taps are still captured and delivered via `PosthogObserver` and explicit SDK calls.
- However, no snapshot frames or visual replay data are generated or transmitted to PostHog, leaving the session recording empty / missing in the PostHog Replay tab.

In this project:
- The legacy shell ([`LegacyApp`](file:///tmp/h-Np2Abb/lib/legacy_app.dart#L8-L25)) wrapped its `MaterialApp` with `PostHogWidget`.
- The redesigned shell ([`NewApp`](file:///tmp/h-Np2Abb/lib/new_app.dart#L19-L37)) returned `MaterialApp.router` directly without wrapping it inside `PostHogWidget`.

## 2. The Fix

In [`lib/new_app.dart`](file:///tmp/h-Np2Abb/lib/new_app.dart):
- Wrapped the returned `MaterialApp.router` with `PostHogWidget(child: ...)`.
- Added an explanatory comment so the wrapper is not accidentally removed in future refactors.
