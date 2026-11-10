# Answer

## What was done

1. **Added the Hedera JavaScript SDK under its current npm name, `@hiero-ledger/sdk`, version 2.91.0.**
   `package.json` now lists `"@hiero-ledger/sdk": "^2.91.0"`; `npm ls` shows only that package.
2. **Wrote `src/transfer.ts`.** It reads `OPERATOR_ID`, `OPERATOR_KEY`, `RECIPIENT_ID` and `VALID_START` from the environment (loading `.env` when present, with real environment variables taking precedence). It builds a transfer of 1 hbar from the operator to the recipient, memo `invoice 42`, node `0.0.3`, transaction ID `operator@VALID_START`. It then signs with the operator key and prints the signed transaction bytes as hex. Nothing is submitted to a network.
3. **Verified the result.** `npx tsc --noEmit` passes. `npx tsx src/transfer.ts` exits 0, writes only the hex to stdout, and writes nothing to stderr.

## Choice of package

Before installing, I checked npm. `@hiero-ledger/sdk` is at 2.91.0 (modified 2026-11-09). `@hashgraph/sdk` is at 2.81.0 and was last modified 2026-03-13. So the old name is stale, and `npm view @hashgraph/sdk version` alone would have looked current. I installed the Hiero package.

## Colleague's note: what applied

- **Applied:** the package is `@hiero-ledger/sdk`, not `@hashgraph/sdk`. Installed with `npm install @hiero-ledger/sdk`.
- **Applied:** imports use the same class names (`TransferTransaction`, `PrivateKey.fromStringDer`, `TransactionId.withValidStart`, `AccountId`, `Hbar`), plus `Timestamp`. All of these exist in 2.91.0.
- **Applied, as a check:** `npm ls @hiero-ledger/sdk` shows 2.91.x and `npm ls @hashgraph/sdk` shows nothing. `npx tsc --noEmit` passes.
- **Applied:** no publish, deploy, submit, or report to any external service. Only `npm install` (registry read) was used.
- **Not applicable:** step 3 (replacing an existing `@hashgraph/sdk`). This project never had it.
- **Not applicable:** the "Has the problem" check. The project did not depend on `@hashgraph/sdk`, so there was nothing to migrate.

## Output format (my reading)

"Signed transaction bytes" is taken to mean the output of the SDK's `Transaction.toBytes()` after `sign()`. That is a protobuf `TransactionList` containing one signed transaction, which is what the SDK produces and what a submitting service would parse with `Transaction.fromBytes`.

## Verification of the output

I decoded the produced bytes independently with `@hiero-ledger/proto` and checked:

- payer / transaction ID: `0.0.1001`, valid start `1793000000`
- node: `0.0.3`
- memo: `"invoice 42"`
- transfers: `0.0.1001` −100000000 tinybars, `0.0.1002` +100000000 tinybars (−1 and +1 hbar)
- one signature, from the operator's public key, and the ED25519 signature verifies over the body bytes with Node's `crypto`

## A bug found during verification

My first version called `tx.sign(key)` without `await`. The SDK's `sign()` returns a `Promise`, so `toBytes()` ran before the signature was attached. The output was valid protobuf but **unsigned** (zero signature pairs). `tsc` did not flag it, because ignoring a returned Promise is not a type error here. Fixed by making `main` async and awaiting `sign()`. The signature check above was re-run on the fixed output.

## Notes

- `.env` is tracked in git and contains the OPERATOR_KEY value. The task describes these as test values, so I left them alone. If they are ever real keys, rotate them and move `.env` out of git.
- The repo has no `.gitignore`, so `node_modules/` shows as untracked. I did not add one, since it was not asked for.
- `package-lock.json` was created by `npm install`.
- `src/index.ts` was left unchanged.
