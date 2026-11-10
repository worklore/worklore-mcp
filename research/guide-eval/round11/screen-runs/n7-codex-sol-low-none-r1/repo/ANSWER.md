# Pollar SDK upgrade

- Updated `@pollar/core` and `@pollar/react` from 0.10.1 to 0.12.0 and refreshed the lockfile.
- Changed the API base URL to the origin; the new SDK adds `/v3` itself.
- Migrated the ARS to Stellar USDC top-up rate from the removed `getRampsQuote` call to `getRampRoutes('ONRAMP')` and `quoteRamp`. The app checks matching routes and displays the best quoted ARS per USDC rate, or no rate when none is available.
- Kept app-sponsored USDC trustlines by using the new default sponsorship behavior, and displayed unreadable balances as unavailable.
- Added the new expired KYC result to the existing status messages.

Verified with `npx tsc --noEmit`.
