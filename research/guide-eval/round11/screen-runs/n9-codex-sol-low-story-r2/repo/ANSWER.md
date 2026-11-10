# Implementation notes

The colleague's note applied to this project: I used Effect 4.1.2 from npm, read the package's bundled `AGENTS.md` and HTTP client example, and used `Context.Service`, `Schema.TaggedError`, and the HTTP client from `effect/http`. The example's `HttpClient.retryTransient` pattern supplies three retries with an exponential schedule; this CLI starts the schedule at 50 ms. I also used the note's recommendation to type-check and verify the CLI against a local server.

The note's `Config.String` rename did not apply because this CLI reads `RATES_URL` directly. I did not install `@effect/platform` because Effect 4 provides the HTTP client in `effect/http`.
