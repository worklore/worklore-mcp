# Upgrade: Pollar 0.10 → 0.12

The app now uses `@pollar/core` and `@pollar/react` `^0.12.0` (0.12.0 is the latest stable release on npm; the
`0.12.1-rc.*` builds are pre-releases, so I did not use them). `npx tsc --noEmit` passes.

## What changed

| File | Change | Why |
| --- | --- | --- |
| `package.json`, `package-lock.json` | Both Pollar packages bumped to `^0.12.0`. | The upgrade itself. |
| `src/pollar.ts` | `baseUrl` is now the bare origin `https://sdk.api.pollar.xyz`, not `…/v1`. | 0.12 adds the API version (`/v3`) itself. The SDK builds `${baseUrl}/v3`, so the old pinned path would have become `/v1/v3`, not the current API. |
| `src/balances.ts` | A `null` balance renders as `USDC unavailable` instead of a number. | In 0.12, `balance` is `string \| null`; `null` means the chain could not be read, not zero. The old `parseFloat(r.balance)` no longer compiled. |
| `src/kyc.ts` | Added `case 'expired'` → `'Verification expired'`. | `KycStatus` gained `'expired'`; the switch had no return for it. |
| `src/trust.ts` | `setTrustline(USDC)` with no options. | `sponsored` no longer exists. In 0.12 the sponsorship is decided server-side from the app's config. Passing `skipSponsorship: true` would have made the user pay, which is the opposite of the old intent. |
| `src/ramp.ts` | Rewritten on `getRampRoutes('ONRAMP')` + `quoteRamp(...)`. Returns `amountIn / amountOut` from the best quote, or `null` when there is no route or no quote. | `getRampsQuote` was removed. The old rate field is replaced by quote amounts. |

Everything the app did is kept: wallet sign-in, the balance list, the KYC wait-and-message, trustline enabling, and the
"Add money" rate line (`1 USDC = X ARS`). `src/Wallet.tsx` and `src/App.tsx` needed no changes.

### The "Add money" quote

The old call named only the country and currency. The new `quoteRamp` requires a `rail` and an asset. Rather than guess a
rail, `bestTopUpRate` looks up the app's own route for ARS → USDC on Stellar from `getRampRoutes('ONRAMP')`, then quotes
with that route's `fiat` and `asset`. If no such route exists it returns `null` without quoting.

## Colleague note: what applied

- **Step 1 (bump packages, fix tsc errors):** applied. The four tsc errors were the ones the note listed.
- **Step 2 (`baseUrl`):** applied, with the origin kept explicit. Reading the 0.12 source, a pinned `/v1` does not keep
  the app on v1; it produces `/v1/v3`. I did not confirm this against the live API.
- **Step 3 (null balance):** applied. Shown as `unavailable`, not `0`, and not `parseFloat(r.balance ?? '0')`.
- **Step 4 (`'expired'` and `setTrustline`):** applied. The `'expired'` message wording is mine.
- **Step 5 (`quoteRamp`):** applied with one change. The note's example hard-codes the fields; I take `rail` and the
  asset identity from the app's route list, so the rail is not guessed. The rate computation (`amountIn / amountOut`),
  the `null` cases, and the `ONRAMP` direction are as the note describes.
- **Verify section:** the tsc check passes. For the other checks I ran compiled code against a stub client (not the live
  API): a `null` balance gives `USDC unavailable`; the stub quote of 10000 ARS in for 8 USDC out gives `1250`; no route
  or no quotes give `null`; `baseUrl` has no path; `'expired'` gives the new message.
- **Ground rules:** nothing was deployed, published, or sent to any external service. No network or API calls were made.

## Not verified

- **Live API.** I did not call sdk-api. The sponsorship behaviour, the ARS route and its rail, and the
  `'expired'`/`'pending'` semantics come from the 0.12 type definitions and README, not from running against the service.
- **Sponsorship setting.** The reserve stays sponsored only if the app's Pollar configuration sponsors trustlines. I
  could not check that setting from the repo.
- **Retirement date.** I did not check the 2026-11-30 retirement against Pollar's announcements.
- **`node_modules/`** is untracked because the repo has no `.gitignore`. I did not add one or commit anything.
