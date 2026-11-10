# Answer: offline hbar transfer with the Hedera/Hiero SDK

## What was done

1. **SDK package.** Added `@hiero-ledger/sdk` at `^2.91.0`, the current version on npm. I did not use `@hashgraph/sdk`. Checking npm showed that `@hashgraph/sdk` was last published as 2.81.0 on 2026-03-13, while `@hiero-ledger/sdk` has releases through 2.91.0 (2026-11-09).
2. **Script.** Wrote `src/transfer.ts`. It:
   - reads `OPERATOR_ID`, `OPERATOR_KEY` (DER-encoded ED25519 hex), `RECIPIENT_ID` and `VALID_START` (Unix seconds) from the environment, loaded through `dotenv`;
   - builds a `TransferTransaction` that moves -1 hbar from the operator and +1 hbar to the recipient, with memo `invoice 42`;
   - sets node `0.0.3` and a transaction ID of `TransactionId.withValidStart(operatorId, VALID_START)`;
   - freezes the transaction without a client, so nothing touches the network;
   - signs with the operator key and prints the signed transaction bytes as one line of hex.
3. **Checks.**
   - `npx tsc --noEmit` passes.
   - `npx tsx src/transfer.ts` exits 0 with no network access. stdout is a single hex line and nothing else; `dotenv` is called with `quiet: true` so it doesn't print its banner.
   - Decoding the output with `Transaction.fromBytes` gives memo `invoice 42`, node `0.0.3`, transaction ID `0.0.1001@1793000000.000000000`, and transfers `0.0.1001: -1 ℏ` and `0.0.1002: +1 ℏ`.
   - The single signature in `sigMap` is an ED25519 signature over the body bytes that verifies against the operator's public key.

## Colleague's note: what applied

- **Applied:** the package moved to `@hiero-ledger/sdk`, and `@hashgraph/sdk` is stale. I confirmed this with `npm view` timestamps, not just the version field. The note's read-only check was the right approach.
- **Applied:** the class and method names are the same (`TransferTransaction`, `PrivateKey.fromStringDer`, `TransactionId.withValidStart`, `AccountId`, `Hbar`). I confirmed each one in the 2.91.0 type declarations, and `tsc` checks them.
- **Applied:** the verification steps. `npm ls @hiero-ledger/sdk` shows 2.91.0, `npm ls @hashgraph/sdk` shows nothing, `tsc` passes, and the output decodes to the expected transaction.
- **Not applicable:** step 3 (replacing an existing `@hashgraph/sdk` dependency). This project had no Hedera SDK installed, so there was nothing to replace.
- **Not applicable:** the note's "reproduce" steps that involve submitting or reporting anything. I did not submit the transaction or publish anything.

## Notes

- `dotenv` resolved to 17.4.2 in the lockfile. That is within the existing `^17.2.0` range, which I left unchanged in `package.json`.
- `package-lock.json` and `node_modules/` were created. The repo has no `.gitignore`, so `node_modules/` appears as untracked. I did not add one, since it wasn't requested.
- `src/index.ts` (which exports `TREASURY_MEMO_PREFIX`) is untouched. The memo is the literal `invoice 42`.
- Nothing has been committed.

## Usage

```sh
# .env supplies OPERATOR_ID, OPERATOR_KEY, RECIPIENT_ID, VALID_START
npx tsx src/transfer.ts > signed.hex
```
