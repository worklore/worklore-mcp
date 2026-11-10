import { config } from "dotenv";
import {
  AccountId,
  PrivateKey,
  TransactionId,
  TransferTransaction,
  Hbar,
  Timestamp,
} from "@hiero-ledger/sdk";

// Load environment variables from a .env file if present.
config();

// Helper to abort with a clear message if a required variable is missing.
function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable ${name}`);
  }
  return value;
}

const operatorId = AccountId.fromString(requireEnv("OPERATOR_ID"));
const operatorKey = PrivateKey.fromStringDer(requireEnv("OPERATOR_KEY"));
const recipientId = AccountId.fromString(requireEnv("RECIPIENT_ID"));
const validStartSec = Number(requireEnv("VALID_START"));
if (Number.isNaN(validStartSec)) {
  throw new Error("VALID_START must be a valid Unix timestamp in seconds");
}

// Build a TransactionId using a Timestamp derived from the Unix seconds.
const txId = TransactionId.withValidStart(
  operatorId,
  Timestamp.fromDate(validStartSec * 1000),
);

// Signing is asynchronous; wrap execution in an async IIFE.
(async () => {
  const tx = await new TransferTransaction()
    .addHbarTransfer(operatorId, new Hbar(-1))
    .addHbarTransfer(recipientId, new Hbar(1))
    .setTransactionMemo("invoice 42")
    .setNodeAccountIds([AccountId.fromString("0.0.3")])
    .setTransactionId(txId)
    .freeze()
    .sign(operatorKey);

  const signedBytes = tx.toBytes();
  console.log(Buffer.from(signedBytes).toString("hex"));
})();
