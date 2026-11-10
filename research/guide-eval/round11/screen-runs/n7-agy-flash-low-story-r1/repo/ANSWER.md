# Pollar SDK Upgrade (0.10 to 0.12)

This document outlines the modifications made to upgrade the application from `@pollar/core` and `@pollar/react` `^0.10.1` to the current SDK version `^0.12.0`.

## Summary of Changes

1. **Dependency Upgrade ([package.json](file:///tmp/h-PQ18ON/package.json))**
   - Upgraded `@pollar/core` and `@pollar/react` from `^0.10.1` to `^0.12.0`.

2. **Base URL Origin Correction ([src/pollar.ts](file:///tmp/h-PQ18ON/src/pollar.ts))**
   - Changed `baseUrl` from `'https://sdk.api.pollar.xyz/v1'` to `'https://sdk.api.pollar.xyz'`.
   - In Pollar SDK 0.12, `baseUrl` represents the bare origin without the API path version, as the SDK appends the API version (`/v3`) internally.

3. **Null Balance Handling ([src/balances.ts](file:///tmp/h-PQ18ON/src/balances.ts))**
   - In 0.12, `WalletBalanceRecord.balance` is typed as `string | null` where `null` indicates that the balance could not be read from the chain.
   - Updated `balanceLines()` so that a `null` balance renders as a dash (`'—'`) rather than converting `null` to `0` or calling `parseFloat(null)`.

4. **KYC Status Handling ([src/kyc.ts](file:///tmp/h-PQ18ON/src/kyc.ts))**
   - Added a case handling the new `'expired'` status value of `KycStatus`, returning `'Verification expired'`.

5. **Trustline Sponsorship Option ([src/trust.ts](file:///tmp/h-PQ18ON/src/trust.ts))**
   - Removed `{ sponsored: true }` from `client.setTrustline(USDC)`, as trustline sponsorship is managed automatically according to the application's configuration in SDK 0.12.

6. **Ramp Quote API Migration ([src/ramp.ts](file:///tmp/h-PQ18ON/src/ramp.ts))**
   - Replaced deprecated `client.getRampsQuote` with `client.quoteRamp`.
   - Updated request parameters to use the new `RampQuoteRequest` format:
     ```ts
     {
       direction: 'ONRAMP',
       fiat: { currency: 'ARS', country: 'AR', rail: 'BANK_TRANSFER' },
       asset: { code: USDC.code, identifier: USDC.issuer, chain: 'STELLAR' },
       amount: { value: pesos.toString(), denomination: 'in' },
     }
     ```
   - Computed the rate (`ARS` per `USDC`) from the best quote (`quotes[0]`) using `amountIn / amountOut`, returning `null` if no quotes are returned.

---

## Evaluation of the Colleague's Note

All 5 areas mentioned in the colleague's note applied directly to this codebase:
- **`baseUrl` pinned path**: Applied to `src/pollar.ts` (removed `/v1`, leaving the bare origin).
- **`null` balance semantics**: Applied to `src/balances.ts` (handled `null` explicitly as a dash rather than defaulting to 0).
- **`KycStatus` `'expired'` value**: Applied to `src/kyc.ts` (handled the new union member in the switch statement).
- **`setTrustline` option cleanup**: Applied to `src/trust.ts` (removed `{ sponsored: true }`).
- **`getRampsQuote` replacement with `quoteRamp`**: Applied to `src/ramp.ts` (migrated to `quoteRamp` and calculated rate as `amountIn / amountOut`).

## Verification
- Ran `npx tsc --noEmit` and `npm run typecheck`, both passing cleanly with 0 errors.
- Verified that no `/v1` or `/v2` references remain in configuration.
- Verified balance line formatting with `null` balances (`'USDC —'`).
- Verified rate calculation formula (`10000 ARS` / `8 USDC` = `1250`).
