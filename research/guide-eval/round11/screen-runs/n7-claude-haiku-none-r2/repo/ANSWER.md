# Pollar upgrade: 0.10.1 → 0.12.0

The app now uses the latest stable Pollar SDK on npm, `@pollar/core` and `@pollar/react` at `^0.12.0`
(`0.12.0` is the `latest` dist-tag; `0.12.1-rc.*` are pre-releases and were not used). `npx tsc --noEmit`
passes.

Versions were checked against the published 0.12.0 type declarations and the package README. The
UPGRADE.md and CHANGELOG.md linked from the README are not in the installed tarball, so they were not read.

## Changes

### `package.json` / `package-lock.json`
- `@pollar/core` and `@pollar/react`: `^0.10.1` → `^0.12.0`.

### `src/pollar.ts`: API base URL
- `baseUrl` was `https://sdk.api.pollar.xyz/v1`. In 0.12 `baseUrl` is the origin only, and the SDK appends
  `/v3` itself. The old value would have produced `/v1/v3` and broken every request.
- Now `https://sdk.api.pollar.xyz`. The API key, network (`testnet`) and the USDC constant are unchanged.

### `src/balances.ts`: wallet balance lines
- `WalletBalanceRecord.balance` is now `string | null`. `null` means the chain could not be read, so it
  now renders as `"<asset> unavailable"` rather than `0.00`.
- The `XLM` label is applied only to native records on Stellar. 0.12 reports balances for every chain the
  app is on, so a native Solana or Polygon coin would otherwise be mislabeled as XLM. For a Stellar-only
  app the output is unchanged.

### `src/kyc.ts`: KYC status
- `KycStatus` gained `'expired'`. It now maps to `"Verification expired"`. The `switch` is still
  exhaustive, so the function still satisfies `noImplicitReturns`.
- `'pending'` is still `"Still being checked"`. In 0.12 `pollKycStatus` also returns `'pending'` at manual
  review, which is the same user-facing state.

### `src/ramp.ts`: "Add money" rate
- `client.getRampsQuote({ country, currency, amount, direction })` no longer exists. 0.12 has
  `getRampRoutes(direction)` and `quoteRamp(body)`, and a quote needs a fiat `rail` plus an asset.
- New flow:
  1. `getRampRoutes('ONRAMP')`, then keep the routes for AR / ARS / USDC on Stellar. This supplies the
     valid `rail` values, so none are hard-coded.
  2. `quoteRamp` for each of those routes, with `amount: { value: String(pesos), denomination: 'in' }`.
  3. Rate = `amountIn / amountOut`, which is pesos per USDC. The result is the lowest rate across all
     quotes, which is the same "best rate" the old `quotes[0].rate` gave.
- The 0.12 response has no `rate` field, so it is derived. When a route has no quote, the API throws
  `SDK_RAMPS_NO_ROUTE` (422). That is caught per route and treated as "no quote from this route".
- If nothing quotes, the function returns `null`, as before.

### `src/trust.ts`: USDC trustline
- `setTrustline(asset, { sponsored: true })` no longer compiles. In 0.12 sponsorship is on by default, and
  `skipSponsorship: true` is the opt-out. The call is now `setTrustline(USDC)`.
- The app still sponsors the reserve. Whether the sponsor pays is set by the app's Pollar dashboard config,
  which the SDK reads server-side, so the behavior depends on that config.
- The return value is unchanged: `true` only when `status === 'success'`.

### Unchanged
- `src/App.tsx`, `src/Wallet.tsx`: no changes were needed. `PollarProvider client={pollarConfig}`,
  `usePollar()` (`wallet`, `walletBalance`, `refreshWalletBalance`, `getClient`, `login`, `isAuthenticated`)
  all still exist with the same shape in 0.12.

## Not verified
- **Not run against the live API.** I did not make network calls to Pollar's service, and there is no dev
  server in this repo. Typecheck is the only check that ran.
- **Ramp amount units.** I assumed `amountIn` and `amountOut` are decimal strings, as `amount.value` is. If
  they are base units, the rate needs scaling. Check one quote response before relying on the number.
- **Ramp rail choice.** The old endpoint took no rail. The new code quotes every AR / ARS / USDC route the
  routes endpoint reports, so the result may come from a different rail than before.
- **API key.** `pub_testnet_tipjar_demo` is unchanged. I could not check that it is still valid for sdk-api
  v3.
- **Unknown behavior changes.** 0.12 adds things this app does not use (wallet provisioning state,
  on-demand wallets, custody modes). Those are not wired up.

## Housekeeping
- `node_modules/` was created by `npm install` and is not ignored by git. The repo has no `.gitignore`.
  I did not add one, since it was not asked for.
