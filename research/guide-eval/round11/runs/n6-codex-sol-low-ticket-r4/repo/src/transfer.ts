import { config } from "dotenv";
import {
  AccountId,
  Hbar,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from "@hiero-ledger/sdk";

config({ quiet: true });

function required(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing ${name}`);
  return value;
}

const operator = AccountId.fromString(required("OPERATOR_ID"));
const recipient = AccountId.fromString(required("RECIPIENT_ID"));
const key = PrivateKey.fromStringDer(required("OPERATOR_KEY"));
const validStart = required("VALID_START");
if (!/^\d+$/.test(validStart) || !Number.isSafeInteger(Number(validStart))) {
  throw new Error("VALID_START must be Unix seconds as a safe integer");
}

const transaction = new TransferTransaction()
  .addHbarTransfer(operator, new Hbar(-1))
  .addHbarTransfer(recipient, new Hbar(1))
  .setTransactionMemo("invoice 42")
  .setNodeAccountIds([AccountId.fromString("0.0.3")])
  .setTransactionId(TransactionId.withValidStart(operator, new Timestamp(Number(validStart), 0)))
  .freeze();

await transaction.sign(key);
process.stdout.write(`${Buffer.from(transaction.toBytes()).toString("hex")}\n`);
