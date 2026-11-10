import { config } from "dotenv";
import {
  AccountId,
  PrivateKey,
  TransactionId,
  TransferTransaction,
  Hbar,
  Timestamp,
} from "@hiero-ledger/sdk";

// Load environment variables from .env
config();

const {
  OPERATOR_ID,
  OPERATOR_KEY,
  RECIPIENT_ID,
  VALID_START,
} = process.env;

if (!OPERATOR_ID || !OPERATOR_KEY || !RECIPIENT_ID || !VALID_START) {
  throw new Error("Missing required environment variables");
}

// Parse accounts and key
const operatorId = AccountId.fromString(OPERATOR_ID);
const recipientId = AccountId.fromString(RECIPIENT_ID);
const operatorKey = PrivateKey.fromStringDer(OPERATOR_KEY);

// Create TransactionId with valid start time from env (seconds since epoch)
const validStartTimestamp = Timestamp.fromDate(new Date(Number(VALID_START) * 1000));
const transactionId = TransactionId.withValidStart(operatorId, validStartTimestamp);

// Build the transfer transaction (offline)
const tx = new TransferTransaction()
  .setTransactionId(transactionId)
  .setNodeAccountIds([new AccountId(0, 0, 3)])
  .addHbarTransfer(operatorId, new Hbar(-1))
  .addHbarTransfer(recipientId, new Hbar(1))
  .setTransactionMemo("invoice 42")
  .freeze();

// Sign with operator private key
tx.sign(operatorKey);

// Output signed transaction bytes as hex
const bytes = tx.toBytes();
console.log(Buffer.from(bytes).toString("hex"));
