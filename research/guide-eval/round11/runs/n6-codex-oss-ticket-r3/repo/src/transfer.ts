import { config } from "dotenv";
import {
  AccountId,
  PrivateKey,
  TransferTransaction,
  Hbar,
  Timestamp,
  TransactionId,
} from "@hiero-ledger/sdk";

// Load environment variables from .env (if present).
config();

// Required environment variables.
const OPERATOR_ID = process.env.OPERATOR_ID;
const OPERATOR_KEY = process.env.OPERATOR_KEY;
const RECIPIENT_ID = process.env.RECIPIENT_ID;
const VALID_START = process.env.VALID_START;

if (!OPERATOR_ID || !OPERATOR_KEY || !RECIPIENT_ID || !VALID_START) {
  throw new Error("Missing required environment variables.");
}

// Parse IDs and key.
const operatorAccount = AccountId.fromString(OPERATOR_ID);
const recipientAccount = AccountId.fromString(RECIPIENT_ID);
const operatorKey = PrivateKey.fromStringDer(OPERATOR_KEY);

// Build a custom transaction ID with the supplied valid start timestamp.
const validStartSec = Number(VALID_START);
const txId = TransactionId.withValidStart(
  operatorAccount,
  new Timestamp(validStartSec, 0)
);

// Create the transfer transaction (1 hbar from operator to recipient).
const transaction = new TransferTransaction()
  .addHbarTransfer(operatorAccount, new Hbar(1)) // debit operator
  .addHbarTransfer(recipientAccount, new Hbar(-1)) // credit recipient
  .setTransactionMemo("invoice 42")
  .setNodeAccountIds([AccountId.fromString("0.0.3")])
  .setTransactionId(txId)
  .sign(operatorKey);

// Encode signed transaction to hex and output.
const signedBytes = transaction.toBytes();
const hex = Buffer.from(signedBytes).toString("hex");
console.log(hex);
