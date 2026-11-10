# Answer

## What was done

1. **SDK added.** `@hashgraph/sdk` was installed at `2.81.0`, the latest version on npm at the time of the change. It is listed in `package.json` as `"^2.81.0"`.

2. **`src/transfer.ts` written.** Run it with `npx tsx src/transfer.ts`. It:
   - reads `OPERATOR_ID`, `OPERATOR_KEY` (DER-encoded ED25519 private key in hex, parsed with `PrivateKey.fromStringDer`), `RECIPIENT_ID` and `VALID_START` (Unix seconds) from the environment, loaded from `.env` via `dotenv/config`;
   - builds a `TransferTransaction` moving 1 hbar (100,000,000 tinybars) from the operator to the recipient, memo `invoice 42`, node account `0.0.3`;
   - sets the transaction ID to `TransactionId.withValidStart(operatorId, VALID_START)`, so the operator's transaction ID carries the valid start from the environment;
   - freezes the transaction, signs it with the operator key, and prints only the signed transaction bytes as hex, followed by a newline.
   
   Nothing is sent to a network. The script builds and signs locally. Missing variables or a non-integer `VALID_START` print an error to stderr and exit with status 1.

3. **Verification.** `npx tsc --noEmit` passes with exit code 0. Running the script with the values from `.env` produced a 403-byte hex string on stdout. I decoded that output with the SDK's `Transaction.fromBytes` and confirmed:
   - memo: `invoice 42`
   - transaction ID: `0.0.1001@1793.000000000`
   - node: `0.0.3`
   - transfers: `0.0.1001 = -100000000`, `0.0.1002 = +100000000`
   - exactly one signature, from the operator's public key

   The check script was temporary and has been deleted.

## Choices I made

- `.env` is loaded with `import "dotenv/config"`. The run's stdout contained only the hex line, so no dotenv log text leaked into the output. Variables already set in the shell take precedence over `.env`, as dotenv does by default.
- The memo is the literal string `invoice 42`. The existing `TREASURY_MEMO_PREFIX` in `src/index.ts` was not used, because the spec asks for this exact memo.
- The hbar amount is hard-coded at 1 hbar, as specified.

## Notes

- `node_modules/` is not in `.gitignore`, and the repo has none, so `git status` will show it as untracked. I did not add one, to keep the change to what was asked.
- `.env` is tracked in git and contains an operator private key. The values are described as test values. If they are ever real, that key should be removed from the repo.
