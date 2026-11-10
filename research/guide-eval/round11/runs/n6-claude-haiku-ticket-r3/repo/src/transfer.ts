import { config } from "dotenv";
import {
  AccountId,
  Hbar,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from "@hiero-ledger/sdk";

// Load .env from the working directory. `quiet` keeps dotenv from writing to stdout,
// so the only thing printed is the signed transaction hex.
config({ quiet: true });

function required(name: string): string {
  const value = process.env[name];
  if (value === undefined || value === "") {
    throw new Error(`Missing required environment variable ${name}`);
  }
  return value;
}

const NODE_ACCOUNT_ID = "0.0.3";
const MEMO = "invoice 42";
const TRANSFER_HBAR = 1;

const operatorId = AccountId.fromString(required("OPERATOR_ID"));
const operatorKey = PrivateKey.fromStringDer(required("OPERATOR_KEY"));
const recipientId = AccountId.fromString(required("RECIPIENT_ID"));

const validStartRaw = required("VALID_START");
const validStartSeconds = Number(validStartRaw);
if (!/^\d+$/.test(validStartRaw) || !Number.isSafeInteger(validStartSeconds)) {
  throw new Error(`VALID_START must be Unix seconds, got "${validStartRaw}"`);
}

// No Client is created, so nothing is sent to a network. Node and transaction ID
// are set explicitly, which is what freezeWith(null) requires.
const transaction = new TransferTransaction()
  .setNodeAccountIds([AccountId.fromString(NODE_ACCOUNT_ID)])
  .setTransactionId(
    TransactionId.withValidStart(operatorId, new Timestamp(validStartSeconds, 0)),
  )
  .setTransactionMemo(MEMO)
  .addHbarTransfer(operatorId, new Hbar(-TRANSFER_HBAR))
  .addHbarTransfer(recipientId, new Hbar(TRANSFER_HBAR))
  .freezeWith(null);

await transaction.sign(operatorKey);

console.log(Buffer.from(transaction.toBytes()).toString("hex"));
