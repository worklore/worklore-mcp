# Upgrade to Current Pollar SDK

This document describes the changes made to upgrade the application from `@pollar/core` and `@pollar/react` version 0.10.1 to the current version `0.12.0`.

## 1. Dependency Upgrade
- Upgraded `@pollar/core` from `^0.10.1` to `^0.12.0` in `package.json` and `package-lock.json`.
- Upgraded `@pollar/react` from `^0.10.1` to `^0.12.0` in `package.json` and `package-lock.json`.

## 2. API Endpoint Configuration (`src/pollar.ts`)
- In Pollar SDK 0.10, `baseUrl` in `PollarClientConfig` specified the full v1 path (`https://sdk.api.pollar.xyz/v1`).
- In Pollar SDK 0.12.0, the SDK targets the `/v3` API version by appending `/v3` to `baseUrl`. `baseUrl` now expects the base origin `https://sdk.api.pollar.xyz`.
- Updated `baseUrl` in `pollarConfig` to `'https://sdk.api.pollar.xyz'`.

## 3. Trustline Sponsorship (`src/trust.ts`)
- In 0.10, `client.setTrustline(asset, { sponsored: true })` was used.
- In 0.12, `setTrustline` sponsors trustlines by default (via server orchestration), and the options parameter now supports `{ limit?: string, skipSponsorship?: boolean }` instead of `{ sponsored: boolean }`.
- Updated `client.setTrustline(USDC)` to rely on default sponsorship.

## 4. Wallet Balances (`src/balances.ts`)
- In 0.12, multichain support made `WalletBalanceRecord.balance` typed as `string | null` (`null` indicating that balance data could not be read).
- Updated `balanceLines` to filter out records where `balance === null` before formatting.

## 5. KYC Status Handling (`src/kyc.ts`)
- In 0.12, `KycStatus` includes the `'expired'` state in addition to `'none' | 'pending' | 'approved' | 'rejected'`.
- Added a `case 'expired': return 'Verification expired';` branch to the switch statement to satisfy TypeScript's non-undefined return type requirement under `noImplicitReturns`.

## 6. Ramp Quotes (`src/ramp.ts`)
- In 0.10, ramps used `client.getRampsQuote({ country, currency, amount, direction })` returning flat `{ rate, ... }` objects.
- In 0.12, the ramp API was restructured around orders and route quotes:
  - Used `client.quoteRamp()` with `{ direction: 'ONRAMP', fiat: { currency: 'ARS', rail: 'BANK_TRANSFER', country: 'AR' }, asset: { code: 'USDC', identifier: null, chain: 'STELLAR' }, amount: { value: pesos.toString(), denomination: 'in' } }`.
  - Calculated the exchange rate (`ARS` per `USDC`) from the best quote (`quotes[0]`) using `parseFloat(bestQuote.amountIn) / parseFloat(bestQuote.amountOut)`.

## Verification
- Ran `npx tsc --noEmit` and `npm run typecheck`, both of which passed with 0 errors.
