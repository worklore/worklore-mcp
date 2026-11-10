# Upgrading Pollar from 0.10 to 0.12

## Summary of Changes

The project was upgraded from `@pollar/core` and `@pollar/react` version `^0.10.1` to `^0.12.0` (specifically `0.12.0` from npm).

### 1. Dependencies (`package.json`, `package-lock.json`)
- Updated `@pollar/core` and `@pollar/react` from `^0.10.1` to `^0.12.0`.

### 2. Base URL Configuration (`src/pollar.ts`)
- Changed `baseUrl` from `'https://sdk.api.pollar.xyz/v1'` to the bare origin `'https://sdk.api.pollar.xyz'`. In Pollar 0.12, the SDK automatically appends the API version (`/v3`); leaving `/v1` causes the client to keep targeting the deprecated API endpoint retiring on 2026-11-30.

### 3. Nullable Wallet Balance (`src/balances.ts`)
- In 0.12, `WalletBalanceRecord.balance` is `string | null`, where `null` indicates that the balance could not be read from the chain (rather than a 0 balance).
- Updated `balanceLines()` so that a `null` balance renders as `'-'` (e.g. `USDC -`), avoiding misleadingly displaying `'0.00'`. Valid string balances continue to be formatted via `parseFloat(r.balance).toFixed(2)`.

### 4. KYC Status Handling (`src/kyc.ts`)
- `KycStatus` in 0.12 includes the `'expired'` state.
- Added a `case 'expired': return 'Expired';` arm to the `switch (status)` block in `kycMessage()`.

### 5. Sponsored Option in Trustline (`src/trust.ts`)
- In 0.12, `client.setTrustline()` removed the `{ sponsored: true }` option since sponsorship is managed server-side by application configuration.
- Simplified `client.setTrustline(USDC, { sponsored: true })` to `client.setTrustline(USDC)`.

### 6. Ramps Quote Migration (`src/ramp.ts`)
- Replaced the deprecated `client.getRampsQuote()` call with `client.quoteRamp()`.
- Built the request with:
  - `direction: 'ONRAMP'`
  - `fiat: { currency: 'ARS', country: 'AR', rail: 'BANK_TRANSFER' }`
  - `asset: { code: USDC.code, identifier: USDC.issuer, chain: 'STELLAR' }`
  - `amount: { value: String(pesos), denomination: 'in' }`
- Computed the top-up rate (fiat per USDC) as `parseFloat(quote.amountIn) / parseFloat(quote.amountOut)` from the best quote (`res.quotes[0]`), returning `null` when no quote is returned or when outputs are invalid.

---

## Which Parts of the Colleague's Note Applied

All parts of the colleague's note applied directly to this codebase:
1. **Pinned `baseUrl`**: Applied to `src/pollar.ts`. Stripping `/v1` to leave the origin `https://sdk.api.pollar.xyz` ensures requests route to the v3 API rather than retiring v1.
2. **Null balance representation**: Applied to `src/balances.ts`. `r.balance === null` was rendered as a dash (`'-'`) rather than defaulting to `0` or `0.00`.
3. **`'expired'` KYC status**: Applied to `src/kyc.ts`. Handled `'expired'` in the status switch statement to satisfy TypeScript exhaustiveness and support expired sessions.
4. **`setTrustline` sponsored option**: Applied to `src/trust.ts`. Removed `{ sponsored: true }` parameter from `setTrustline()`.
5. **Ramp quote rewriting**: Applied to `src/ramp.ts`. Replaced `getRampsQuote` with `quoteRamp` and calculated the exchange rate as `amountIn / amountOut` (e.g., 10,000 ARS in for 8 USDC out gives rate 1,250), returning `null` if no quotes exist.

---

## Verification
- Ran `npx tsc --noEmit` and `npm run typecheck`; both passed cleanly with exit code 0.
