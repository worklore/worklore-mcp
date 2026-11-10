# Answer

## What was done

- Added the Hedera JavaScript SDK as `@hiero-ledger/sdk` at `2.91.0`, the current npm version. `package.json` now lists it under `dependencies`; `package-lock.json` was created by the install.
- Wrote `src/transfer.ts`, run with `npx tsx src/transfer.ts`. It:
  - reads `OPERATOR_ID`, `OPERATOR_KEY` (DER-encoded ED25519 private key, hex), `RECIPIENT_ID` and `VALID_START` (Unix seconds) from the environment, loaded from `.env` via the existing `dotenv` dependency;
  - builds a `TransferTransaction` moving -1 hbar from the operator and +1 hbar to the recipient, memo `invoice 42`, node `0.0.3`, transaction ID `TransactionId.withValidStart(operator, VALID_START)`;
  - freezes it, signs it with the operator key, and prints only the hex of `toBytes()`.
- It makes no network calls: no `Client` is created, and the transaction is frozen with an explicit node and transaction ID.
- The memo reuses `TREASURY_MEMO_PREFIX` ("invoice") exported from the existing `src/index.ts`, so the text is `${TREASURY_MEMO_PREFIX} 42`.

## Verification

- `npx tsc --noEmit` passes with exit code 0.
- `npx tsx src/transfer.ts` with the `.env` test values prints a 361-byte hex string and exits 0.
- I decoded the output with the SDK and protobuf packages, outside the repo, and checked:
  - transaction ID `0.0.1001@1793000000.000000000`;
  - node `0.0.3`;
  - memo `invoice 42`;
  - transfers `0.0.1001 -100000000` and `0.0.1002 100000000` tinybar (-1 and +1 hbar);
  - one signature, valid under the operator's public key, and the signer's public key prefix matches the operator key.

## Colleague's note: what applied

- **Applied:** the Hedera SDK was published under `@hiero-ledger/sdk`, and npm does not say so for `@hashgraph/sdk`. I confirmed it with `npm view` release times: `@hiero-ledger/sdk` 2.91.0, modified 2026-11-09; `@hashgraph/sdk` last modified 2026-03-13 at 2.81.0. I used `@hiero-ledger/sdk`.
- **Applied:** the class and method names are the same (`PrivateKey.fromStringDer`, `TransactionId.withValidStart`, `AccountId`, `Hbar`, `TransferTransaction`). I confirmed them against the installed 2.91.0 typings.
- **Applied:** `npm ls @hiero-ledger/sdk` shows 2.91.0, and `npm ls @hashgraph/sdk` shows nothing.
- **Did not apply:** step 3, replacing an existing `@hashgraph/sdk` dependency. The project never had it.
- **Did not apply:** the note's `DER` key example and `Client`-based flow. The task asked for an offline script.

## Things to know

- `.env` is not in git's ignore list, and there is no `.gitignore`. `.env` holds `OPERATOR_KEY`. The values there are test values, but a real key would be committed if this repo is committed as is. I did not add a `.gitignore` because the task did not ask for one.
- `node_modules/` and `package-lock.json` are also untracked. I left them as they are.
- `npm install` printed warnings that some packages (`protobufjs`, `esbuild`, `fsevents`) have install scripts not covered by an allow policy. The script runs without them, so I did not change that setting.
