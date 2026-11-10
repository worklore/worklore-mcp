# Pollar SDK upgrade

- Upgraded `@pollar/core` and `@pollar/react` to the current npm release, 0.12.0, and updated the lockfile.
- Removed the pinned `/v1` `baseUrl`; the SDK now supplies its own API version path.
- Kept wallet balances visible while showing an unreadable (`null`) balance as `unavailable`, rather than zero.
- Added the `expired` KYC message and removed the obsolete trustline `sponsored` option. Trustline sponsorship now follows the Pollar app configuration.
- Migrated the Argentine peso top-up quote to `quoteRamp` for Stellar USDC, using the first (best) quote. The displayed ARS per USDC rate is `amountIn / amountOut`; absent or invalid quotes return `null`.

The colleague's note applied to all five changes: the versioned URL, null balances, expired KYC status, trustline sponsorship option, and ramp quote API and rate calculation. This app has no adapter packages or other ramp order flow to migrate.

Verification: `npx tsc --noEmit` and `git diff --check` pass. No `/v1` or `/v2` `baseUrl` remains in `src`. The rate calculation gives 1250 for 10000 ARS in and 8 USDC out.
