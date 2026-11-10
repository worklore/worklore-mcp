# Upgrading Pollar 0.10 to 0.12

Target: `@pollar/core` and `@pollar/react` at `^0.12.0` (npm `latest` is 0.12.0; the `next` tag is an rc).
`npx tsc --noEmit` passes. The app's behavior is kept; the changes below are what 0.12 required.

## Changes

| File | Change |
| --- | --- |
| `package.json`, `package-lock.json` | `@pollar/core` and `@pollar/react` `^0.10.1` → `^0.12.0`. |
| `src/pollar.ts` | `baseUrl` is now the origin `https://sdk.api.pollar.xyz`, without `/v1`. The SDK adds the version (`/v3` in 0.12). The host is the same as the 0.12 default. |
| `src/balances.ts` | `balance` is `string \| null`. A null balance now renders as `USDC unavailable` instead of parsing to a number. |
| `src/kyc.ts` | Added the `'expired'` case: `Verification expired`. |
| `src/trust.ts` | `setTrustline(USDC)` without `{ sponsored: true }`. The option no longer exists. |
| `src/ramp.ts` | `getRampsQuote` (removed) replaced by `getRampRoutes` + `quoteRamp`. The rate is `amountIn / amountOut` of the best quote, or `null` when there is none. |

`src/Wallet.tsx` and `src/App.tsx` needed no changes.

## What each change does now

- **Balances:** same lines as before (`XLM 12.50`, `USDC 12.50`). Only a null balance differs: it shows `unavailable`, not `0.00`.
- **KYC:** same mapping as before, plus `expired`.
- **Trustline:** the USDC trustline is still sponsored by default when eligible. The 0.12 API has no per-call `sponsored: true`; it decides from the app's Pollar settings, and `skipSponsorship` is the only opt-out. See the caveat below.
- **Add money:** still quotes 10,000 ARS in and shows `1 USDC = {rate} ARS`. The rate is `amountIn / amountOut` from the best quote (e.g. 10000 in, 8 out → 1250).

## Colleague's note: what applied

1. **Install and fix tsc: applied.** The four tsc errors were the ones the note predicted: `balance` as `string | null`, `getRampsQuote` removed, `sponsored` removed from `setTrustline`, and the new `'expired'` KYC status (tsc reported it as a missing return).
2. **Pinned `baseUrl`: applied.** I set the bare origin rather than removing the key. The 0.12 default is the same host, so the pin does not change where requests go. I checked this in the installed `@pollar/core` source (`https://sdk.api.pollar.xyz` + `/v3`).
3. **Null balance: applied.** I render `unavailable`; I did not use `parseFloat(r.balance ?? '0')`.
4. **`'expired'` and `setTrustline` without `sponsored`: applied.**
5. **`quoteRamp`: applied with two differences.**
   - The note's example hard-codes `fiat.rail`, but the note does not say which rail Argentina uses, and the package does not document one. `bestTopUpRate` now finds the ARS/AR/USDC/STELLAR route in `getRampRoutes('ONRAMP')` and uses its `fiat` and `asset` objects. It returns `null` when no such route exists.
   - `asset.identifier` comes from that route rather than from `USDC.issuer`. I could not confirm which identifier format the API expects, so I used the value the API itself reports.

## Not applied / not in the note

- The note's "Wrong fix" (`parseFloat(r.balance ?? '0')`) was not used.
- I did not read Pollar's `UPGRADE.md`: it is not in the installed package, and I had no network access to GitHub. The changes come from the installed type definitions and the package README (its 0.11.1 and 0.12.0 notes).

## Verification

- `npx tsc --noEmit`: passes (exit 0).
- No `/v1`, `/v2`, `sponsored`, or `getRampsQuote` remains in `src/`.
- A scratch run (compiled outside the repo, against stub clients):
  - `balance: null` renders as `USDC unavailable`; a balance of `12.5` renders as `XLM 12.50`.
  - Quote of 10000 ARS in, best quote 10000 in / 8 out → rate `1250`; no routes → `null`.
  - KYC maps `approved`, `rejected`, `pending`, `none`, `expired` to the expected messages.
  - `setTrustline` receives only the asset, with no options.
- **Not verified:** nothing was run against the live API, so the v1 retirement, the testnet demo key, the ARS route, and the quote values are untested. Before 2026-11-30, run the wallet, KYC, trustline and Add money flows against sdk-api.

## Caveats and things left unchanged

- **Sponsorship:** the old `sponsored: true` forced the app to sponsor. Now sponsorship follows the app's Pollar settings. If the dashboard turns sponsorship off, the user pays the trustline reserve, which the old code would not have allowed. Check the setting before release.
- **Multichain balances:** 0.12 returns balances for every chain the app is provisioned on, and `balanceLines` shows all of them. The app is Stellar-only, so this does not arise today. If a Solana or Polygon wallet is added, its native coin would be labelled `XLM` (because `type === 'native'`), and a token with the same code would appear as a second line. Label by `chain` before enabling other chains.
- **`node_modules/`** is not ignored by this repo (there is no `.gitignore`). It was created by `npm install` and is not committed.
- I did not commit anything, and I did not publish or deploy anything.
