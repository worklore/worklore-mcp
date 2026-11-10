# Offline HBAR transfer with the Hedera/Hiero JavaScript SDK

## What was done

1. **Chose the SDK package.** `@hashgraph/sdk` stops at 2.81.0 (last modified 2026-03-13, not deprecated on npm). The project now uses `@hiero-ledger/sdk`, the current package, at `2.91.0` (the latest on npm as of 2026-11-09). `package.json` has `"@hiero-ledger/sdk": "^2.91.0"`. `@hashgraph/sdk` is not installed.
2. **Wrote `src/transfer.ts`.** It reads `OPERATOR_ID`, `OPERATOR_KEY` (DER hex), `RECIPIENT_ID` and `VALID_START` from the environment (loaded from `.env` via dotenv, quietly). It builds a `TransferTransaction` that moves -1 ℏ from the operator and +1 ℏ to the recipient, with memo `invoice 42`, node `0.0.3`, and transaction ID `TransactionId.withValidStart(operator, VALID_START)`. It signs with the operator key and prints only the hex of `toBytes()`.
3. **Offline by construction.** No `Client` is created, so nothing is sent to any network. `freezeWith(null)` requires the node account ID and transaction ID to be set explicitly, and the script sets both.

## How to run

```
npx tsx src/transfer.ts
```

It prints one line of hex (360 hex characters for the `.env` test values). Errors go to stderr and exit non-zero.

## Verification

- `npx tsc --noEmit` passes with exit 0.
- `npx tsx src/transfer.ts` exits 0 with nothing on stderr.
- The output decodes with `Transaction.fromBytes` to:
  - transaction ID `0.0.1001@1793000000.000000000`
  - node `0.0.3`
  - memo `"invoice 42"`
  - transfers `0.0.1001 -1 ℏ` and `0.0.1002 +1 ℏ`
- The single signature in the transaction is from the operator's public key and verifies over the body bytes.

## Colleague's note: what applied and what did not

- **Applied:** The old `@hashgraph/sdk` is superseded by `@hiero-ledger/sdk`. I confirmed this on npm: the old package stopped at 2.81.0 in March 2026, while the new one has releases through 2.91.0. I used the new package and its `import` path. The class names used (`TransferTransaction`, `PrivateKey.fromStringDer`, `TransactionId.withValidStart`, `AccountId`, `Hbar`) exist in 2.91.0 under the same names.
- **Applied, with a change to the check:** `npm view @hashgraph/sdk version` does print `2.81.0`, so it does not reveal the move. Checking `npm view ... time.modified` and the list of `@hiero-ledger/sdk` versions did.
- **Not applicable:** The project had no existing `@hashgraph/sdk` dependency or imports to replace, and no second SDK to remove. This was a fresh add.
- **Not used:** The colleague's specific dates and version numbers were not taken on trust. I checked them against npm directly.

## Notes

- `npm install` printed warnings that some packages (`esbuild`, `protobufjs`, `fsevents`) have install scripts not yet approved. `tsx` runs fine, so I did not change anything. Run `npm install-scripts ls` if you want to review them.
- There is no `.gitignore`. `node_modules/` and `package-lock.json` show as untracked. Nothing was committed.
- `src/index.ts` was left unchanged.
