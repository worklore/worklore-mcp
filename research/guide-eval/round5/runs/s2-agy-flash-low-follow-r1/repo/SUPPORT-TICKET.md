# Ticket #4471: no session replays since the redesign

Reported by product, 2026-10-16.

Replay tab in PostHog shows sessions only from users still on the old UI
(the A/B group). Users on the new UI appear in Events (screens, taps,
`loan_amount_changed`, `application_submitted` all arrive) but have no
recording. Project settings: Record user sessions = on, sampling 100%,
minimum duration 0. Same posthog_flutter version for both groups, same build.
