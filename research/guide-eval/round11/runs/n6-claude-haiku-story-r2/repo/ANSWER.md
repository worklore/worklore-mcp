# Answer: offline HBAR transfer with the Hedera SDK

## What I did

1. **Chose the package.** The Hedera JavaScript SDK now publishes as
   `@hiero-ledger/sdk`. On npm, `@hiero-ledger/sdk` is at 2.91.0 (modified
   2026-11-09). `@hashgraph/sdk` stopped at 2.81.0 (last modified 2026-03-13)
   and still shows as `latest`. I installed `@hiero-ledger/sdk@^2.91.0`.
2. **Wrote `src/transfer.ts`.** It:
   - reads `OPERATOR_ID`, `OPERATOR_KEY` (DER-encoded ED25519 private key),
     `RECIPIENT_ID` and `VALID_START` (Unix seconds);
   - builds a `TransferTransaction` moving 1 HBAR from the operator to the
     recipient, memo `invoice 42`, node `0.0.3`, and transaction ID
     `<OPERATOR_ID>@<VALID_START>`;
   - freezes it offline (no client, no network), signs it with the operator
     key, and prints the signed bytes as hex.
3. **Verified it.** Ran `npx tsc --noEmit` (passes) and `npx tsx src/transfer.ts`
   (exit 0, prints one hex line). Nothing is submitted to any network.

## Run it

```
npx tsx src/transfer.ts
```

The script loads `.env` through `dotenv` (already a project dependency).
Variables already set in the shell take precedence over `.env`.

## Verification of the output

I decoded the hex with the same SDK and checked:

- transaction ID: `0.0.1001@1793000000.000000000`
- node: `0.0.3`
- memo: `invoice 42`
- transfers: `0.0.1001 -1 ℏ`, `0.0.1002 +1 ℏ`
- one signature, from the operator's public key, verifies over the body bytes
  with `publicKey.verify`.

My first verification script reported `false`. That was a bug in the check
script (it read the signature map through the wrong accessor), not in the
transaction. Reading `sigMap.sigPair` directly gives a match, and a fresh
`PrivateKey.sign(body)` returns the same bytes as the stored signature.

## Changes to the project

- `package.json`: added `"@hiero-ledger/sdk": "^2.91.0"` under `dependencies`.
- `package-lock.json`: created by `npm install`.
- `src/transfer.ts`: new.
- `ANSWER.md`: this file.
- `node_modules/`: installed dependencies (not committed).

I did not commit anything.

## Colleague's note: what applied

- **Applied: use `@hiero-ledger/sdk`, not `@hashgraph/sdk`.** Confirmed with
  `npm view`: the newer package is the one with recent releases (2.91.0 vs
  2.81.0, last change 2026-03-13). I installed only `@hiero-ledger/sdk`.
- **Applied: the same class names work.** `TransferTransaction`,
  `PrivateKey.fromStringDer`, `TransactionId.withValidStart`, `AccountId`
  and `Hbar` all exist in 2.91.0 with the expected signatures, so no code
  changes were needed beyond the import path.
- **Applied: verification steps.** `npm ls @hiero-ledger/sdk` shows 2.91.0,
  and `npm ls @hashgraph/sdk` shows nothing. `npx tsc --noEmit` passes, and
  the output decodes to the expected transaction.
- **Not applicable: step 3 (replace an existing `@hashgraph/sdk`).** The
  project had no Hedera SDK installed before this change, so there was
  nothing to replace or remove.
- **Not applicable: reproduction prerequisites and sources.** They describe
  the colleague's own setup. I did not use their steps beyond the install and
  import, and I did not rely on their code.

## Notes

- `.env` holds test values and is not listed in `.gitignore`. I did not add
  it to git. You may want to add it to `.gitignore` before committing.
- `npm install` printed warnings that `protobufjs` and `esbuild` have install
  scripts that npm has not approved. These are not errors. They did not affect
  the build or the run.
