# Hedera SDK Setup and Transfer Implementation

## What Was Done

1. **Hedera SDK Package Installation**:
   - Following the guidance that the Hedera JavaScript SDK transitioned under the Hiero project name, `@hiero-ledger/sdk` was installed (`^2.91.0`) instead of the discontinued `@hashgraph/sdk`.
   - Verified that `@hiero-ledger/sdk` is installed and `@hashgraph/sdk` is not present in `package.json` / `node_modules`.

2. **Implemented `src/transfer.ts`**:
   - Loads environment variables from `.env` using `dotenv/config`.
   - Reads:
     - `OPERATOR_ID`: parsed with `AccountId.fromString(process.env.OPERATOR_ID)`.
     - `OPERATOR_KEY`: parsed with `PrivateKey.fromStringDer(process.env.OPERATOR_KEY)` for the DER-encoded hex ED25519 key.
     - `RECIPIENT_ID`: parsed with `AccountId.fromString(process.env.RECIPIENT_ID)`.
     - `VALID_START`: parsed as a Unix seconds timestamp using `new Timestamp(Number(process.env.VALID_START), 0)`.
   - Constructs a transaction ID: `TransactionId.withValidStart(operatorId, validStart)`.
   - Builds an offline transaction using `TransferTransaction`:
     - Configured node ID `0.0.3` via `.setNodeAccountIds([AccountId.fromString("0.0.3")])`.
     - Sets memo to `"invoice 42"` via `.setTransactionMemo("invoice 42")`.
     - Adds transfers: `-1` hbar from operator and `+1` hbar to recipient.
     - Freezes the transaction (`freeze()`).
   - Signs the transaction offline using `tx.sign(operatorKey)`.
   - Converts the signed transaction to bytes (`signedTx.toBytes()`) and outputs only the signed transaction bytes as a hex string via `console.log(Buffer.from(txBytes).toString("hex"))`.

3. **Validation**:
   - `npx tsc --noEmit` compiles cleanly with zero errors.
   - `npx tsx src/transfer.ts` runs and outputs the hex string.
   - Deserialization and offline verification check confirmed the transaction ID, node account ID (`0.0.3`), memo (`invoice 42`), amounts (-1 / +1 Hbar), and Ed25519 signature by the operator public key.

---

## Application of the Colleague's Note

The colleague's note discussed the rename and migration from `@hashgraph/sdk` to `@hiero-ledger/sdk`:

- **Applied**:
  - **Package selection**: Used `@hiero-ledger/sdk` rather than `@hashgraph/sdk` to ensure we are using the current version of the Hedera SDK.
  - **API usage**: Used SDK classes (`TransferTransaction`, `PrivateKey.fromStringDer`, `TransactionId.withValidStart`, `AccountId`, `Hbar`) from `@hiero-ledger/sdk`.
  - **Verification**: Verified `@hiero-ledger/sdk` is installed (`npm ls @hiero-ledger/sdk` shows 2.91.0) and `@hashgraph/sdk` is empty (`npm ls @hashgraph/sdk` shows empty).

- **Ignored / Did not apply**:
  - The migration steps regarding removing existing `@hashgraph/sdk` dependencies and replacing existing imports, as this was a fresh integration where `@hashgraph/sdk` was not previously present.
