# Upgrade to Pollar 0.12

The app moves from `@pollar/core` and `@pollar/react` `^0.10.1` to `^0.12.0`, the current npm release, because
sdk-api v1 (which 0.10 calls) retires on 2026-11-30. `npx tsc --noEmit` passes. Every screen keeps the behavior it had,
except where noted below.

## What changed

**Dependencies** (`package.json`, `package-lock.json`): both Pollar packages bumped to `^0.12.0`.

**`src/pollar.ts`: pinned `baseUrl`** (silent change, found by reading the 0.12 dist, not by tsc)
- Was `https://sdk.api.pollar.xyz/v1`. In 0.12 the SDK builds `${baseUrl}/v3` itself, so the old value would have
  produced `/v1/v3`.
- Now `https://sdk.api.pollar.xyz`, the bare origin.

**`src/balances.ts`: null balance**
- `WalletBalanceRecord.balance` is `string | null`. `null` means the chain could not be read.
- A `null` balance now renders as `USDC unavailable` (or `XLM unavailable`) instead of a number.
- A real `'0'` still renders as `USDC 0.00`. The old `parseFloat(r.balance ?? '0')` fix was not used.

**`src/kyc.ts`: `'expired'`**
- `KycStatus` gained `'expired'`. The switch now returns `Verification expired` for it, so the function still
  returns on every path (`noImplicitReturns`).

**`src/trust.ts`: trustline sponsorship**
- `setTrustline` no longer accepts `sponsored`. The call is now `client.setTrustline(USDC)`.
- Behavior change: the app used to request sponsorship on every call. In 0.12 the server decides who pays, from the
  app's sponsorship config. See "Needs checking" below.

**`src/ramp.ts`: "Add money" quote**
- `getRampsQuote` was removed. The function now:
  1. Calls `getRampRoutes('ONRAMP')` and finds the route for AR / ARS / USDC on STELLAR. If there is none, it returns
     `null`.
  2. Calls `quoteRamp` with that route's `fiat` and `asset`, `direction: 'ONRAMP'`, and
     `amount: { value: String(pesos), denomination: 'in' }`.
  3. Takes the best quote (quotes come best first). Rate = `Number(amountIn) / Number(amountOut)`, pesos per USDC.
     It returns `null` if there is no quote or the rate is not finite.
- The return type and the UI (`1 USDC = {rate} ARS`) are unchanged.

**Not changed:** `src/App.tsx`, `src/Wallet.tsx` (no type errors, and the behavior they depend on is the same).

## Verification

- `npx tsc --noEmit`: passes (it reported 4 errors after the bump alone, all fixed above).
- Ran the changed functions against stub clients, compiled into a scratch directory that was then deleted:
  - `baseUrl` is `https://sdk.api.pollar.xyz`, and the SDK's own base path is `${baseUrl}/v3`.
  - `balanceLines` with `balance: null` gives `USDC unavailable`. A `'0'` gives `USDC 0.00`.
  - `kycMessage` gives `Verification expired` for `'expired'`, and the other four statuses are unchanged.
  - `bestTopUpRate` with a quote of 10000 ARS in / 8 USDC out returns `1250`. With no AR/ARS route, or with no quote, it
    returns `null` and does not call `quoteRamp`.
  - `enableUsdc` calls `setTrustline` with the USDC asset and no options; it returns `true` on `status: 'success'`.
- Not verified: no live call to the sdk-api. The sandbox has no API credentials and this app runs as a mounted widget.

## Colleague's note: what applied

- **Step 1 (install and tsc)**: applied. The four tsc errors match the note.
- **Step 2 (`baseUrl`)**: applied. The note says `/v2`, but in the 0.12 dist the SDK targets `/v3`. The fix is the same
  (bare origin), and the code does not hard-code a version.
- **Step 3 (null balance as a dash/unavailable)**: applied, with the text "unavailable" rather than a dash.
- **Step 4 (`'expired'`, `setTrustline` without `sponsored`)**: applied.
- **Step 5 (`quoteRamp` rewrite and rate)**: applied, with one change. The note hard-codes the `rail`. The API requires a
  rail value from its enum, and I did not know the right one for Argentina. So the code takes the rail from the
  AR/ARS route that `getRampRoutes` returns. Rate formula and null-when-no-quote are as in the note.
- **Verify section**: applied. The 1250 check passes. The `/v1` and `/v2` check passes: none remain in `src/`.
- **Ground rules**: followed. Nothing was deployed, published, or sent anywhere. The only network calls were the npm
  registry lookup and install.
- **UPGRADE.md**: not used. It is not shipped in the npm packages, so I worked from the installed type definitions and
  READMEs.

## Needs checking

1. **Trustline sponsorship.** The old code forced sponsorship on each call. Now the app's dashboard sponsorship setting
   decides. If that setting does not sponsor trustlines, users will pay the reserve. Check the setting for this app
   before relying on the "app sponsors the reserve" behavior.
2. **Ramp rail.** The "Add money" quote uses whatever rail the AR/ARS route reports. If Pollar lists several AR/ARS
   routes, the first one is used. Confirm that is the rail you want.
3. **Extra request.** "Add money" now makes two calls (routes, then quote) instead of one.
4. **`node_modules/`** is untracked and there is no `.gitignore` in the repo. Nothing was committed.
