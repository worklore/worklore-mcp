# Hedera transfer signing script

## What was done

1. **SDK added.** `@hashgraph/sdk` was installed at `2.81.0`, the current `latest` on npm (checked with `npm view`). It is listed under `dependencies` in `package.json`, and `package-lock.json` was created.

2. **`src/transfer.ts` written.** Run with `npx tsx src/transfer.ts`. It:
   - reads `OPERATOR_ID`, `OPERATOR_KEY` (DER-encoded ED25519 private key, hex), `RECIPIENT_ID` and `VALID_START` (Unix seconds) from the environment, loaded from `.env` via `dotenv`. A missing variable or a non-integer `VALID_START` stops the script with an error.
   - builds a `TransferTransaction` that moves 1 hbar from the operator to the recipient (-1 hbar from the operator, +1 hbar to the recipient, in tinybars), with memo `invoice 42`;
   - sets node account `0.0.3`;
   - sets the transaction ID to `TransactionId.withValidStart(operatorId, Timestamp(VALID_START, 0))`;
   - freezes it with `freezeWith(null)`, so no client is created and nothing is fetched from the network;
   - signs it with the operator key and prints the signed transaction bytes as one line of hex. Nothing else goes to stdout.

3. **Type check.** `npx tsc --noEmit` passes.

## How it was verified

- The script runs offline and prints one hex line.
- I decoded the output with the SDK's protobuf types and checked:
  - memo is `invoice 42`;
  - transaction ID is `0.0.1001@1793000000.000000000`, matching `VALID_START=1793000000`;
  - node is `0.0.3`;
  - transfers are `0.0.1001: -100000000` and `0.0.1002: +100000000` tinybars (1 hbar);
  - one signature is present, its public key prefix matches the operator key, and the ED25519 signature verifies over the body bytes.

## Issue found during verification

My first version called `tx.sign(key)` without `await`. In SDK 2.81 `sign()` is async, so the bytes were serialized before the signature was added. The output had no signature pair. The fix was `await tx.sign(operatorKey)`. The verification above was run on the fixed script.

## Choices I made

- The memo text is written as the literal `"invoice 42"`. `src/index.ts` exports `TREASURY_MEMO_PREFIX = "invoice"`, but I did not import it, to keep `transfer.ts` self-contained.
- `freezeWith(null)` is used for offline freezing. It is valid here because the node account and transaction ID are both set explicitly.
- The key is read with `PrivateKey.fromStringDer`, so only DER-hex keys are accepted, as specified.

## Things to be aware of

- `.env` is **tracked by git**, and `.gitignore` does not exist. It contains `OPERATOR_KEY`, a private key. The value is described as a test value, but if it is a real key it should be removed from the repo and rotated. I did not change it.
- `node_modules/` is untracked and should be ignored; a `.gitignore` would help.
- Nothing was submitted, published or sent to any external service. No changes were committed.
