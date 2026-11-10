import { config } from "dotenv";
import {
  AccountId,
  Hbar,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from "@hiero-ledger/sdk";

// Load .env into process.env. `quiet` keeps dotenv from printing a banner to stdout.
config({ quiet: true });

function requireEnv(name: string): string {
  const value = process.env[name];
  if (value === undefined || value === "") {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

const operatorId = AccountId.fromString(requireEnv("OPERATOR_ID"));
const operatorKey = PrivateKey.fromStringDer(requireEnv("OPERATOR_KEY"));
const recipientId = AccountId.fromString(requireEnv("RECIPIENT_ID"));

const validStartSeconds = Number(requireEnv("VALID_START"));
if (!Number.isSafeInteger(validStartSeconds) || validStartSeconds < 0) {
  throw new Error("VALID_START must be a non-negative integer Unix timestamp in seconds");
}

const NODE_ACCOUNT_ID = AccountId.fromString("0.0.3");

const transaction = new TransferTransaction()
  .setTransactionId(
    TransactionId.withValidStart(
      operatorId,
      Timestamp.fromDate(new Date(validStartSeconds * 1000)),
    ),
  )
  .setNodeAccountIds([NODE_ACCOUNT_ID])
  .addHbarTransfer(operatorId, new Hbar(-1))
  .addHbarTransfer(recipientId, new Hbar(1))
  .setTransactionMemo("invoice 42");

// Passing null is safe here: node account IDs and transaction ID are already set,
// so freezing needs no network client and nothing is submitted.
transaction.freezeWith(null);
await transaction.sign(operatorKey);

console.log(Buffer.from(transaction.toBytes()).toString("hex"));
