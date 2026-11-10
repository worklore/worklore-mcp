# Upgrading Pollar SDK to 0.12.0

## 1. SDK Version Update
- Updated `@pollar/core` and `@pollar/react` from `^0.10.1` to `^0.12.0` (latest available on npm).
- Updated `package.json` and `package-lock.json` via `npm install @pollar/core@latest @pollar/react@latest`.

## 2. API Endpoint & Base URL Configuration (`src/pollar.ts`)
- Removed the deprecated `baseUrl: 'https://sdk.api.pollar.xyz/v1'` parameter from `pollarConfig`.
- Pollar 0.12.0 defaults to the modern `/v3` API endpoints (`https://sdk.api.pollar.xyz/v3`), avoiding the retiring v1 API.

## 3. Balance Records (`src/balances.ts`)
- In Pollar 0.12, `WalletBalanceRecord.balance` is typed as `string | null` (where `null` indicates an unreadable chain RPC).
- Filtered out records with `null` balances before parsing and formatting, ensuring safe execution and type safety.

## 4. KYC Status Enum Handling (`src/kyc.ts`)
- Updated `kycMessage` to handle the new `'expired'` status variant in the `KycStatus` union type (`'none' | 'pending' | 'approved' | 'rejected' | 'expired'`), ensuring exhaustive return coverage under TypeScript's `noImplicitReturns`.

## 5. Trustline Sponsorship Options (`src/trust.ts`)
- In Pollar 0.12, trustlines are sponsored by default. The obsolete option `{ sponsored: true }` was removed from `client.setTrustline(USDC)`.

## 6. Ramp Quote Migration (`src/ramp.ts`)
- Migrated from deprecated `client.getRampsQuote` to `client.quoteRamp`:
  - Uses the current POST request schema: `direction: 'ONRAMP'`, fiat details (`country: 'AR'`, `currency: 'ARS'`, `rail: 'BANK_TRANSFER'`), asset details (`code: USDC.code`, `identifier: USDC.issuer`, `chain: 'STELLAR'`), and amount (`{ value: String(pesos), denomination: 'in' }`).
  - Calculates the exchange rate (ARS per 1 USDC) from the top-quoted route via `parseFloat(amountIn) / parseFloat(amountOut)`, returning `null` when no quote exists.
