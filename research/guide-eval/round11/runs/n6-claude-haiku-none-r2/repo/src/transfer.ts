import "dotenv/config";
import {
  AccountId,
  Hbar,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from "@hashgraph/sdk";
import { TREASURY_MEMO_PREFIX } from "./index.ts";

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

const nodeAccountId = AccountId.fromString("0.0.3");

const transaction = new TransferTransaction()
  .addHbarTransfer(operatorId, new Hbar(-1))
  .addHbarTransfer(recipientId, new Hbar(1))
  .setTransactionMemo(`${TREASURY_MEMO_PREFIX} 42`)
  .setNodeAccountIds([nodeAccountId])
  .setTransactionId(
    TransactionId.withValidStart(
      operatorId,
      new Timestamp(validStartSeconds, 0),
    ),
  )
  .freeze();

await transaction.sign(operatorKey);

console.log(Buffer.from(transaction.toBytes()).toString("hex"));
