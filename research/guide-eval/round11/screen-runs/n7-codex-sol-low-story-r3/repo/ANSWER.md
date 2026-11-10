# Pollar upgrade

Upgraded `@pollar/core` and `@pollar/react` from 0.10.1 to the current npm release, 0.12.0, and updated the lockfile. Removed the pinned `/v1` `baseUrl` so the SDK selects its current API path.

The wallet still shows each asset balance, with an unreadable (`null`) balance shown as `unavailable` rather than zero. KYC now has a message for `expired`. The USDC trustline call uses the 0.12 signature; reserve sponsorship follows the Pollar app configuration. The Add money action finds a live ARS to Stellar USDC onramp route and quotes 10,000 ARS through `quoteRamp`. It derives the displayed ARS per USDC rate from `amountIn / amountOut`, returning `null` if there is no route, no quote, or no positive output amount.

The colleague's note applied to the package upgrade, the pinned URL, null balances, expired KYC, trustline options, and replacement ramp quote API. The fixed payment rail in its example did not apply: this app selects the rail from available routes.

Verification: `npx tsc --noEmit` passes. A source search found no remaining `/v1` or `/v2` base URL, old quote call, or `sponsored` option.
