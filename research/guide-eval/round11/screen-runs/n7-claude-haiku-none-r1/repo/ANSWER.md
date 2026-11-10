# Pollar 0.10 → 0.12 upgrade

The app now depends on `@pollar/core` and `@pollar/react` **^0.12.0** (latest on npm at the time of the upgrade).
`npx tsc --noEmit` passes.

## Why the app broke

- **API version.** 0.10 talks to `/v1`. In 0.12 `baseUrl` is an origin only, and the SDK appends `/v3` itself
  (`${baseUrl || "https://sdk.api.pollar.xyz"}/v3`). The old `baseUrl: '.../v1'` would have produced `.../v1/v3`,
  so it now points at the origin.
- **Ramp quotes were replaced.** `getRampsQuote` no longer exists. Ramps are now routes (`getRampRoutes`) and quotes
  (`quoteRamp`), and quotes carry `amountIn` / `amountOut` instead of a `rate`.
- **Trustline sponsorship flag removed.** `setTrustline` no longer accepts `sponsored`. Sponsorship is on by default.
- **KYC has a new status.** `pollKycStatus` returns `'expired'` as well as the four statuses 0.10 had.
- **Balances can be `null`.** `WalletBalanceRecord.balance` is `string | null`; `null` means the chain could not be read.

## What changed, file by file

| File | Change |
| --- | --- |
| `package.json`, `package-lock.json` | `@pollar/core` and `@pollar/react` → `^0.12.0`. |
| `src/pollar.ts` | `baseUrl` is `https://sdk.api.pollar.xyz` (origin only). API key, network and USDC asset unchanged. |
| `src/trust.ts` | `setTrustline(USDC)` without `{ sponsored: true }`. Still returns `true` only on `status === 'success'`. |
| `src/balances.ts` | A `null` balance renders as `"<CODE> unavailable"` instead of `NaN`. The XLM label for native balances is unchanged. |
| `src/kyc.ts` | `'expired'` → `"Verification expired"`. `'pending'` (which now also covers manual review) still shows "Still being checked". |
| `src/ramp.ts` | "Add money" rewritten on top of `getRampRoutes('ONRAMP')` + `quoteRamp` (details below). |
| `src/App.tsx`, `src/Wallet.tsx` | No change needed: `PollarProvider`, `usePollar`, `login`, `walletBalance`, `refreshWalletBalance`, `getClient` all still exist with the same shape. |

### "Add money" (`src/ramp.ts`)

The old call asked for ARS quotes and used the first quote's `rate`. The new flow:

1. `getRampRoutes('ONRAMP')`, then keep the routes that are ARS / country `AR` / USDC on Stellar. For a Stellar
   asset the `identifier` is the issuer address, which is how `src/ramp.ts` matches it (the SDK's own
   `rampTrustlineAsset` reads it the same way).
2. `quoteRamp` once per matching route, with `amount: { value: pesos, denomination: 'in' }` (pesos are spent, so the
   user's amount is fixed and the USDC received is quoted).
3. Rate = `amountIn / amountOut` (ARS per USDC) for each quote. The lowest rate wins, and the function returns `null`
   if nothing quotes. `SDK_RAMPS_NO_ROUTE` (422) counts as "no quote" for that rail. Other errors are rethrown.

The result is the same kind of number as before: ARS per 1 USDC, now including the fees in the quote.

## Behaviour changes to know about

- **Sponsorship now comes from the app's dashboard config.** The SDK no longer takes a per-call "sponsor this"
  flag. Sponsorship is on by default and the server decides, "when eligible". If the dashboard does not sponsor
  USDC trustlines, the user pays the reserve and fee themselves. The old `sponsored: true` was a request; it is now
  implicit, so check the dashboard setting.
- **The balance list has every enabled asset on every chain** (0.11+ multichain), not only Stellar. The labels are
  just `r.code`, so a USDC on another chain would show the same label as the Stellar USDC. This app runs on
  Stellar testnet only, so I left the labels alone; add the chain to the label if you enable other chains.
- **Fiat rail choice.** The quote uses the rails the routes list for ARS. The route order decides nothing: the
  cheapest quote wins across all rails.

## Not verified

- **No live calls.** I had no network access or test credentials here, so I checked the code against the 0.12
  type declarations and the SDK's own source, not against the API. Run the "Add money", "Accept USDC" and KYC
  buttons against testnet before the cutover.
- **No UPGRADE.md.** The package README points to an `UPGRADE.md` for migration steps, but it is not in the npm
  tarball, so I worked from the README notes and the type declarations.
- **CORS.** 0.12 sends an `x-pollar-sdk` header on every request. The README says the API must list it in CORS
  `allowHeaders`. If the creator's site is served from a different origin, check that the Pollar side allows it.
- **`node_modules/` is untracked.** The repo has no `.gitignore`, so `git status` shows it. I did not add one.
