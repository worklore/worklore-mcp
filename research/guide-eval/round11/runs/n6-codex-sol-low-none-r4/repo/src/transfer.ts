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
  if (!value) throw new Error(`Missing ${name}`);
  return value;
}

const operatorId = AccountId.fromString(required("OPERATOR_ID"));
const recipientId = AccountId.fromString(required("RECIPIENT_ID"));
const operatorKey = PrivateKey.fromStringDer(required("OPERATOR_KEY"));
const validStart = Number(required("VALID_START"));
if (!Number.isSafeInteger(validStart) || validStart < 0) {
  throw new Error("VALID_START must be a nonnegative Unix timestamp in seconds");
}

const transaction = new TransferTransaction()
  .addHbarTransfer(operatorId, new Hbar(-1))
  .addHbarTransfer(recipientId, new Hbar(1))
  .setTransactionMemo("invoice 42")
  .setNodeAccountIds([AccountId.fromString("0.0.3")])
  .setTransactionId(TransactionId.withValidStart(operatorId, new Timestamp(validStart, 0)))
  .freeze();

await transaction.sign(operatorKey);
process.stdout.write(Buffer.from(transaction.toBytes()).toString("hex") + "\n");
