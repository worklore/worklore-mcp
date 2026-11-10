# Pollar SDK upgrade

- Updated `@pollar/core` and `@pollar/react` from 0.10.1 to 0.12.0 and refreshed the npm lockfile.
- Removed the hardcoded `/v1` API URL. The current SDK uses its default endpoint and calls `/v3`.
- Updated the ARS top-up quote to use 0.12 ramp routes and quotes. It selects Argentine peso routes for Stellar USDC and returns the best ARS-per-USDC rate, or `null` when none can be quoted.
- Kept USDC trustline sponsorship by using the SDK's default server-side sponsorship; removed the obsolete `sponsored` option.
- Displayed unreadable balances as unavailable and handled expired KYC status explicitly.

Verified with `npx tsc --noEmit` (passes).
