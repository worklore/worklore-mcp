# Ticket #4471: missing replay frames on the new UI

The redesign's `NewApp` returned `MaterialApp.router` without a `PostHogWidget` around it. The old `LegacyApp` already had that wrapper. On Flutter mobile, `PostHogWidget` supplies the screen frames used by session replay, so the new UI could send events while producing no replay video.

I wrapped the new `MaterialApp.router` in `PostHogWidget` and added a comment explaining why it is required. Both app shells now have the wrapper. The shared setup already enables replay (`config.sessionReplay = true`), and both routers already include `PosthogObserver`, so neither needed a change.

From the colleague's note, the missing wrapper on a second app shell and the recommendation to document it applied. The suggested replay enablement, navigation observer, and text masking checks were already satisfied in this code. Console settings and sampling were ruled out by the ticket; no configuration change was needed.

Verification: `flutter analyze` passed with no issues. A device session and its appearance in PostHog cannot be verified from this repository alone; after building the new UI, navigate several screens, background the app to flush, and check that the replay shows frames.
