import "dotenv/config";
import {
  AccountId,
  Hbar,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from "@hiero-ledger/sdk";

const NODE_ACCOUNT_ID = "0.0.3";
const MEMO = "invoice 42";

function required(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`missing environment variable ${name}`);
  }
  return value;
}

const operatorId = AccountId.fromString(required("OPERATOR_ID"));
const operatorKey = PrivateKey.fromStringDer(required("OPERATOR_KEY"));
const recipientId = AccountId.fromString(required("RECIPIENT_ID"));

const validStartRaw = required("VALID_START");
if (!/^\d+$/.test(validStartRaw)) {
  throw new Error("VALID_START must be a Unix timestamp in whole seconds");
}
const validStart = new Timestamp(Number(validStartRaw), 0);

// Built and frozen offline: the node account and transaction ID are set
// explicitly, so no client (and no network) is needed.
const transaction = new TransferTransaction()
  .addHbarTransfer(operatorId, new Hbar(-1))
  .addHbarTransfer(recipientId, new Hbar(1))
  .setTransactionMemo(MEMO)
  .setNodeAccountIds([AccountId.fromString(NODE_ACCOUNT_ID)])
  .setTransactionId(TransactionId.withValidStart(operatorId, validStart))
  .freezeWith(null);

await transaction.sign(operatorKey);

process.stdout.write(Buffer.from(transaction.toBytes()).toString("hex") + "\n");
