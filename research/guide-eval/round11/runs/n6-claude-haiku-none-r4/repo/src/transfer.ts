import "dotenv/config";
import {
  AccountId,
  Hbar,
  HbarUnit,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from "@hashgraph/sdk";

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing environment variable ${name}`);
  }
  return value;
}

const operatorId = AccountId.fromString(requireEnv("OPERATOR_ID"));
const operatorKey = PrivateKey.fromStringDer(requireEnv("OPERATOR_KEY"));
const recipientId = AccountId.fromString(requireEnv("RECIPIENT_ID"));

const validStartSeconds = Number(requireEnv("VALID_START"));
if (!Number.isSafeInteger(validStartSeconds) || validStartSeconds < 0) {
  throw new Error("VALID_START must be a non-negative integer (Unix seconds)");
}

const nodeAccountId = AccountId.fromString("0.0.3");

const transaction = new TransferTransaction()
  .addHbarTransfer(operatorId, Hbar.from(-1, HbarUnit.Hbar))
  .addHbarTransfer(recipientId, Hbar.from(1, HbarUnit.Hbar))
  .setTransactionMemo("invoice 42")
  .setNodeAccountIds([nodeAccountId])
  .setTransactionId(
    TransactionId.withValidStart(
      operatorId,
      new Timestamp(validStartSeconds, 0),
    ),
  );

// Offline: freeze without a Client (node and transaction ID are already set).
transaction.freezeWith(null);
await transaction.sign(operatorKey);

const bytes = await transaction.toBytesAsync();
console.log(Buffer.from(bytes).toString("hex"));
