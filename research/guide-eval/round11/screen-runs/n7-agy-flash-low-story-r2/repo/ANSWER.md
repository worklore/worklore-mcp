# Upgrade to Pollar SDK 0.12.0

## Summary of Changes

Upgraded `@pollar/core` and `@pollar/react` from `^0.10.1` to `^0.12.0` in [package.json](file:///tmp/h-GsVisO/package.json) to migrate away from Pollar's retiring sdk-api v1.

### 1. SDK Package Bump ([package.json](file:///tmp/h-GsVisO/package.json), [package-lock.json](file:///tmp/h-GsVisO/package-lock.json))
- Updated `@pollar/core` and `@pollar/react` dependencies to `^0.12.0`.

### 2. Config Endpoint ([src/pollar.ts](file:///tmp/h-GsVisO/src/pollar.ts))
- Removed the pinned path `/v1` from `baseUrl`: updated from `'https://sdk.api.pollar.xyz/v1'` to `'https://sdk.api.pollar.xyz'`. In 0.12, `baseUrl` is only the origin, and the SDK attaches the version prefix (`/v3`) automatically.

### 3. Null Balance Handling ([src/balances.ts](file:///tmp/h-GsVisO/src/balances.ts))
- In 0.12, `WalletBalanceRecord.balance` is typed as `string | null`, where `null` signifies an unreadable chain state rather than zero. Updated `balanceLines()` to render `'unavailable'` when `balance === null`, instead of defaulting to `'0'`.

### 4. KYC Status Extension ([src/kyc.ts](file:///tmp/h-GsVisO/src/kyc.ts))
- `KycStatus` includes `'expired'`. Added a case handling `'expired'` that returns `'Verification expired'`.

### 5. Sponsored Option in Trustline ([src/trust.ts](file:///tmp/h-GsVisO/src/trust.ts))
- In 0.12, `setTrustline()` dropped the `{ sponsored: boolean }` option (the application sponsorship settings determine who pays). Removed `{ sponsored: true }` and called `client.setTrustline(USDC)`.

### 6. Ramps Quote Migration ([src/ramp.ts](file:///tmp/h-GsVisO/src/ramp.ts))
- Replaced deprecated `client.getRampsQuote()` with `client.quoteRamp()`.
- Configured parameters:
  - `direction: 'ONRAMP'`
  - `fiat: { currency: 'ARS', country: 'AR', rail: 'BANK_TRANSFER' }`
  - `asset: { code: USDC.code, identifier: USDC.issuer, chain: 'STELLAR' }`
  - `amount: { value: String(pesos), denomination: 'in' }`
- Computed rate from the top quote as `parseFloat(best.amountIn) / parseFloat(best.amountOut)` (pesos per USDC), returning `null` when no quote is returned.

---

## Colleague's Note: What Applied vs Ignored

All parts of the colleague's note applied directly to this upgrade:

1. **Pinned `baseUrl` (`baseUrl: 'https://sdk.api.pollar.xyz/v1'`)**:
   - **Applied**: Changed to origin `https://sdk.api.pollar.xyz` without `/v1`. Leaving `/v1` compiles but quietly continues targeting the retiring API endpoint.
2. **Null balance representation**:
   - **Applied**: Rendered `balance: null` as `'unavailable'` in `balanceLines()` rather than parsing `'0'`.
3. **`KycStatus` handling `'expired'`**:
   - **Applied**: Added handling for `'expired'` in `kycMessage()`.
4. **`setTrustline` options change**:
   - **Applied**: Removed `{ sponsored: true }` parameter from `setTrustline()`.
5. **Ramp quote rewritten to `quoteRamp`**:
   - **Applied**: Replaced `getRampsQuote` with `quoteRamp({ direction: 'ONRAMP', ... })` and calculated the exchange rate as `amountIn / amountOut`, returning `null` if no quote is available.
