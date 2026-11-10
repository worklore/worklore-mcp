import "dotenv/config";
import {
  AccountId,
  Hbar,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from "@hashgraph/sdk";

function required(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing environment variable ${name}`);
  }
  return value;
}

const operatorId = AccountId.fromString(required("OPERATOR_ID"));
const operatorKey = PrivateKey.fromStringDer(required("OPERATOR_KEY"));
const recipientId = AccountId.fromString(required("RECIPIENT_ID"));
const validStartSeconds = Number(required("VALID_START"));

if (!Number.isSafeInteger(validStartSeconds) || validStartSeconds < 0) {
  throw new Error("VALID_START must be a non-negative integer (Unix seconds)");
}

const nodeId = AccountId.fromString("0.0.3");

const tx = new TransferTransaction()
  .addHbarTransfer(operatorId, Hbar.fromTinybars(-100_000_000))
  .addHbarTransfer(recipientId, Hbar.fromTinybars(100_000_000))
  .setTransactionMemo("invoice 42")
  .setNodeAccountIds([nodeId])
  .setTransactionId(
    TransactionId.withValidStart(
      operatorId,
      new Timestamp(validStartSeconds, 0),
    ),
  )
  .freeze();

const signed = await tx.sign(operatorKey);
const bytes = signed.toBytes();

console.log(Buffer.from(bytes).toString("hex"));
