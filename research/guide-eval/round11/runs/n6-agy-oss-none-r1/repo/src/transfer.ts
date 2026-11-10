import { AccountId, PrivateKey, Hbar, TransferTransaction, TransactionId, Timestamp } from "@hashgraph/sdk";
import * as dotenv from "dotenv";
import { Buffer } from "buffer";

dotenv.config();

// Load environment variables
const operatorIdStr = process.env.OPERATOR_ID;
const operatorKeyDerHex = process.env.OPERATOR_KEY;
const recipientIdStr = process.env.RECIPIENT_ID;
const validStartStr = process.env.VALID_START;

if (!operatorIdStr || !operatorKeyDerHex || !recipientIdStr || !validStartStr) {
  console.error("Missing required environment variables.");
  process.exit(1);
}

// Parse values
const operatorId = AccountId.fromString(operatorIdStr);
const operatorKey = PrivateKey.fromStringDer(operatorKeyDerHex);
const recipientId = AccountId.fromString(recipientIdStr);
const validStartSec = Number(validStartStr);
if (isNaN(validStartSec)) {
  console.error("VALID_START must be a number.");
  process.exit(1);
}

// Build TransactionId with custom valid start timestamp using Timestamp (seconds, nanos)
// Removed duplicate Timestamp import
const txId = new TransactionId(operatorId, new Timestamp(validStartSec, 0));

// Build the transfer transaction (offline, no client needed)
const transaction = new TransferTransaction()
  .setTransactionId(txId)
  .setNodeAccountIds([new AccountId(0, 0, 3)])
  .setTransactionMemo("invoice 42")
  .addHbarTransfer(operatorId, new Hbar(-1)) // send 1 hbar
  .addHbarTransfer(recipientId, new Hbar(1)); // receive 1 hbar

// Sign with operator key
transaction.sign(operatorKey);

// Serialize signed transaction to bytes and output as hex
const bytes = transaction.toBytes();
const hex = Buffer.from(bytes).toString("hex");
console.log(hex);
