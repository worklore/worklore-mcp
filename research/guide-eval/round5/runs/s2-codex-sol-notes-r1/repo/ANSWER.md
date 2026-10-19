# Ticket #4471

The new UI's `MaterialApp.router` was missing the `PostHogWidget` wrapper. The old UI has that wrapper, which explains why its sessions have replays while the new UI's events still arrive without recordings. Shared SDK setup already enables session replay, and both shells have a `PosthogObserver`; neither was the cause.

Wrapped the new UI's `MaterialApp.router` in `PostHogWidget` and added a comment explaining its role. The router and analytics configuration are unchanged.

Verified the code change with `dart format`, `git diff --check`, and a source inspection of both app shells. The formatter reported that `flutter_lints` could not be resolved because dependencies have not been fetched in this workspace; formatting still completed. A device or emulator run is still needed to confirm that a new UI session appears in PostHog Session replay with visible frames after navigating and backgrounding the app; this workspace does not include a device run or PostHog access.
