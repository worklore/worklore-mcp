# loanly

Flutter app (iOS + Android). Two UI shells ship at the moment:

- `lib/legacy_app.dart` — the old UI, still used by ~30% of users
  (`--dart-define=NEW_UI=false` in the release pipeline for the A/B group).
- `lib/new_app.dart` — the redesigned UI with go_router (default).

Analytics: PostHog (`posthog_flutter`). Events, screen tracking and session
replay are enabled in `lib/analytics.dart`; "Record user sessions" is on in
the PostHog project settings, sampling 100%.

```
flutter run --dart-define=NEW_UI=true
flutter run --dart-define=NEW_UI=false
```
