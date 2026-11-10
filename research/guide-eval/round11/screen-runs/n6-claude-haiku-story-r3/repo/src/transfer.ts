import "dotenv/config";
import {
  AccountId,
  Hbar,
  HbarUnit,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from "@hiero-ledger/sdk";
import { TREASURY_MEMO_PREFIX } from "./index.ts";

function required(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`missing environment variable ${name}`);
  }
  return value;
}

function unixSeconds(name: string): number {
  const raw = required(name);
  if (!/^\d+$/.test(raw)) {
    throw new Error(`${name} must be Unix seconds, got "${raw}"`);
  }
  return Number(raw);
}

const operatorId = AccountId.fromString(required("OPERATOR_ID"));
const operatorKey = PrivateKey.fromStringDer(required("OPERATOR_KEY"));
const recipientId = AccountId.fromString(required("RECIPIENT_ID"));
const validStart = new Timestamp(unixSeconds("VALID_START"), 0);
const nodeId = AccountId.fromString("0.0.3");

const transaction = new TransferTransaction()
  .setNodeAccountIds([nodeId])
  .setTransactionId(TransactionId.withValidStart(operatorId, validStart))
  .setTransactionMemo(`${TREASURY_MEMO_PREFIX} 42`)
  .addHbarTransfer(operatorId, Hbar.from(-1, HbarUnit.Hbar))
  .addHbarTransfer(recipientId, Hbar.from(1, HbarUnit.Hbar))
  .freeze();

await transaction.sign(operatorKey);

console.log(Buffer.from(transaction.toBytes()).toString("hex"));
