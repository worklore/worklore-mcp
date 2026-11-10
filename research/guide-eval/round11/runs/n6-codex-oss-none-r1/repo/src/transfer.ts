import { AccountId, PrivateKey, TransactionId, TransferTransaction, Hbar, Timestamp } from "@hashgraph/sdk";
import { config } from "dotenv";

// Load environment variables from a .env file if present.
config();

/** Helper to read a required environment variable or throw. */
function requireEnv(name: string): string {
  const val = process.env[name];
  if (val == null || val === "") {
    throw new Error();
  }
  return val;
}

// Required inputs
const operatorId = AccountId.fromString(requireEnv("OPERATOR_ID"));
// OPERATOR_KEY is a DER‑encoded Ed25519 private key expressed as hex.
const operatorKey = PrivateKey.fromStringDer(requireEnv("OPERATOR_KEY"));
const recipientId = AccountId.fromString(requireEnv("RECIPIENT_ID"));
const validStartSeconds = Number(requireEnv("VALID_START"));

// Build a TransactionId with the desired valid start timestamp.
// Timestamp expects numeric seconds and nanos as numbers.
const customTimestamp = new Timestamp(validStartSeconds, 0);
const txId = new TransactionId(operatorId, customTimestamp);

// Create a transfer of exactly 1 hbar (1 000 000 000 tinybars).
const ONE_HBAR_TINYBARS = 1_000_000_000n;
const transferTx = new TransferTransaction()
  .setTransactionId(txId)
  .setNodeAccountIds([AccountId.fromString("0.0.3")])
  .addHbarTransfer(operatorId, Hbar.fromTinybars(-ONE_HBAR_TINYBARS))
  .addHbarTransfer(recipientId, Hbar.fromTinybars(ONE_HBAR_TINYBARS))
  .setTransactionMemo("invoice 42");

// Freeze and sign the transaction offline.
const signedTx = await transferTx.freeze().sign(operatorKey);

// Output signed transaction bytes as a hex string.
console.log(Buffer.from(signedTx.toBytes()).toString("hex"));
