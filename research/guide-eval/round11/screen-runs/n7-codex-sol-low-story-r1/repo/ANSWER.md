# Pollar SDK upgrade

- Updated `@pollar/core` and `@pollar/react` from 0.10.1 to the current stable npm release, 0.12.0, and refreshed the lockfile. The app still uses Pollar for sign-in, wallet balances, USDC trustlines, KYC status, and the Add money quote.
- Removed the pinned `/v1` `baseUrl`. The 0.12 SDK selects its current API path from the default origin.
- Displayed an unreadable (`null`) balance as `unavailable`, rather than zero. Added the `expired` KYC message.
- Updated `setTrustline` to the new signature. Reserve sponsorship now follows the Pollar app configuration.
- Replaced `getRampsQuote` with route discovery and `quoteRamp` for ARS onramps to the configured Stellar USDC asset. The displayed ARS per USDC rate is `amountIn / amountOut`; the lowest valid rate wins, and no valid quote returns `null`.

The colleague's note applied to the package upgrade, pinned API URL, null balance, expired KYC status, removed trustline option, and new quote API. This app discovers the available fiat rail from Pollar routes because it has no fixed rail in its existing configuration.

Verification: `npx tsc --noEmit` passes. A quote of 10,000 ARS in and 8 USDC out produces 1,250 ARS per USDC by the new calculation.
