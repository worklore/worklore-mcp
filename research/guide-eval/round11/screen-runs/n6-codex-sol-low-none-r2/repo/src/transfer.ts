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
  if (!value) throw new Error(`${name} is required`);
  return value;
}

const operatorId = AccountId.fromString(required("OPERATOR_ID"));
const recipientId = AccountId.fromString(required("RECIPIENT_ID"));
const operatorKey = PrivateKey.fromStringDer(required("OPERATOR_KEY"));
const validStartText = required("VALID_START");
if (!/^\d+$/.test(validStartText)) {
  throw new Error("VALID_START must be Unix seconds");
}
const validStart = Number(validStartText);
if (!Number.isSafeInteger(validStart)) {
  throw new Error("VALID_START is outside the safe integer range");
}

const transaction = new TransferTransaction()
  .addHbarTransfer(operatorId, new Hbar(-1))
  .addHbarTransfer(recipientId, new Hbar(1))
  .setTransactionMemo("invoice 42")
  .setNodeAccountIds([AccountId.fromString("0.0.3")])
  .setTransactionId(
    TransactionId.withValidStart(operatorId, new Timestamp(validStart, 0)),
  )
  .freeze();

await transaction.sign(operatorKey);
process.stdout.write(Buffer.from(transaction.toBytes()).toString("hex") + "\n");
