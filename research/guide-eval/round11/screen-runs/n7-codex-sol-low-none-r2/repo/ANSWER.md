# Pollar SDK upgrade

- Updated `@pollar/core` and `@pollar/react` from 0.10.1 to 0.12.0 and refreshed the npm lockfile.
- Removed the hardcoded `/v1` API URL. Pollar 0.12 uses its default API origin with `/v3`.
- Migrated the ARS top-up quote to route discovery and `quoteRamp`, selecting Stellar USDC quotes and computing the best ARS per USDC rate. A missing or unquotable route returns `null`.
- Kept sponsored USDC trustlines by using the new default sponsorship behavior, handled expired KYC as failed verification, and show unavailable balances without displaying them as zero.

Verified with `npx tsc --noEmit`.
