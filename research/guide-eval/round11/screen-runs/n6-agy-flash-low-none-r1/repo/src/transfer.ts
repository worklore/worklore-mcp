import "dotenv/config";
import {
  AccountId,
  Hbar,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from "@hashgraph/sdk";

const operatorIdStr = process.env.OPERATOR_ID;
const operatorKeyStr = process.env.OPERATOR_KEY;
const recipientIdStr = process.env.RECIPIENT_ID;
const validStartStr = process.env.VALID_START;

if (!operatorIdStr || !operatorKeyStr || !recipientIdStr || !validStartStr) {
  throw new Error(
    "Missing required environment variables: OPERATOR_ID, OPERATOR_KEY, RECIPIENT_ID, VALID_START"
  );
}

const operatorId = AccountId.fromString(operatorIdStr);
const recipientId = AccountId.fromString(recipientIdStr);
const operatorKey = PrivateKey.fromStringED25519(operatorKeyStr);

const validStartSec = Number(validStartStr);
if (Number.isNaN(validStartSec)) {
  throw new Error(`Invalid VALID_START timestamp: ${validStartStr}`);
}

const validStart = new Timestamp(validStartSec, 0);
const transactionId = TransactionId.withValidStart(operatorId, validStart);

const transaction = new TransferTransaction()
  .setTransactionId(transactionId)
  .setNodeAccountIds([AccountId.fromString("0.0.3")])
  .addHbarTransfer(operatorId, new Hbar(-1))
  .addHbarTransfer(recipientId, new Hbar(1))
  .setTransactionMemo("invoice 42")
  .freeze();

await transaction.sign(operatorKey);

const signedBytes = transaction.toBytes();
console.log(Buffer.from(signedBytes).toString("hex"));
