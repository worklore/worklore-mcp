import "dotenv/config";
import {
  AccountId,
  PrivateKey,
  TransferTransaction,
  TransactionId,
  Hbar,
  Timestamp,
} from "@hiero-ledger/sdk";

// Load environment variables (expects a .env file at project root).
const {
  OPERATOR_ID,
  OPERATOR_KEY,
  RECIPIENT_ID,
  VALID_START,
} = process.env;

if (!OPERATOR_ID || !OPERATOR_KEY || !RECIPIENT_ID || !VALID_START) {
  throw new Error("Missing required environment variables");
}

const operatorId = AccountId.fromString(OPERATOR_ID);
const operatorKey = PrivateKey.fromStringDer(OPERATOR_KEY);
const recipientId = AccountId.fromString(RECIPIENT_ID);
// Convert Unix seconds to a Timestamp (seconds, nanos=0).
const validStart = Timestamp.fromDate(new Date(Number(VALID_START) * 1000));

const transactionId = TransactionId.withValidStart(operatorId, validStart);

const tx = new TransferTransaction()
  .addHbarTransfer(operatorId, new Hbar(-1))
  .addHbarTransfer(recipientId, new Hbar(1))
  .setTransactionId(transactionId)
  .setTransactionMemo("invoice 42")
  .setNodeAccountIds([new AccountId(0, 0, 3)])
  .freeze();

tx.sign(operatorKey);

// Output signed transaction bytes as hex string.
const signedBytes = tx.toBytes();
console.log(Buffer.from(signedBytes).toString("hex"));
