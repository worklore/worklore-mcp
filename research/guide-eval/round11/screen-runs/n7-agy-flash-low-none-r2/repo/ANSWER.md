# Pollar SDK Upgrade (0.10.1 to 0.12.0)

## Overview
Upgraded `@pollar/core` and `@pollar/react` from version `0.10.1` to `0.12.0` (the current latest release from npm), updating the API configuration, KYC status handling, trustline creation, balance formatting, and ramp quoting to match the `/v3` API and SDK contract.

## Changes Made

1. **`package.json` & `package-lock.json`**:
   - Upgraded `@pollar/core` and `@pollar/react` dependencies to `^0.12.0`.
   - Updated package-lock and installed npm dependencies.

2. **`src/pollar.ts`**:
   - Changed `baseUrl` from `'https://sdk.api.pollar.xyz/v1'` to `'https://sdk.api.pollar.xyz'`. The 0.12.0 SDK targets `/v3` automatically using the origin URL (appending `/v3` internally), retiring the old `/v1` endpoint.

3. **`src/balances.ts`**:
   - Updated `balanceLines()` to safely handle `record.balance: string | null`. In 0.11+, multichain balances return `null` if a network/RPC cannot be read. Formats valid balances to 2 decimal places and renders `—` when null.

4. **`src/kyc.ts`**:
   - Added handling for `'expired'` to the switch statement over `KycStatus` (`'none' | 'pending' | 'approved' | 'rejected' | 'expired'`), returning `'Verification expired'`.

5. **`src/trust.ts`**:
   - In 0.12.0, trustlines are sponsored by default via the server endpoint (or opted out via `skipSponsorship: true`), removing the deprecated `{ sponsored: true }` option on `client.setTrustline(USDC)`.

6. **`src/ramp.ts`**:
   - Replaced deprecated `client.getRampsQuote()` with `client.getRampRoutes('ONRAMP')` and `client.quoteRamp()`.
   - Discovers the ARS -> USDC (Stellar) route and queries a live quote with exact-in denomination for the given ARS amount.
   - Calculates the effective exchange rate (`amountIn / amountOut`, i.e., ARS per 1 USDC) matching the display format in `Wallet.tsx` (`1 USDC = <rate> ARS`). Returns `null` if no quote or route is available.

## Verification
- Verified compilation with `npx tsc --noEmit` and `npm run typecheck`, both passing with 0 errors.
