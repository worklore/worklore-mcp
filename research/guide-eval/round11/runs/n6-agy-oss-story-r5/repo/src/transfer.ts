// src/transfer.ts
// Offline Hedera HBAR transfer signing script
// Reads configuration from .env and prints the signed transaction bytes as hex.

import "dotenv/config";
import {
  TransferTransaction,
  TransactionId,
  AccountId,
  Hbar,
  PrivateKey,
} from "@hiero-ledger/sdk";

// Environment variables (example values are provided in .env)
const {
  OPERATOR_ID,
  OPERATOR_KEY,
  RECIPIENT_ID,
  VALID_START,
} = process.env;

if (!OPERATOR_ID || !OPERATOR_KEY || !RECIPIENT_ID || !VALID_START) {
  console.error(
    "Missing required environment variables: OPERATOR_ID, OPERATOR_KEY, RECIPIENT_ID, VALID_START"
  );
  process.exit(1);
}

// Parse IDs and key
const operatorAccount = AccountId.fromString(OPERATOR_ID);
const recipientAccount = AccountId.fromString(RECIPIENT_ID);

// DER‑encoded hex private key
const operatorKey = PrivateKey.fromStringDer(OPERATOR_KEY);

// Build a TransactionId with the user‑supplied valid start (Unix seconds)
const validStartDate = new Date(Number(VALID_START) * 1000);
const txId = TransactionId.withValidStart(operatorAccount, validStartDate);

// Build the transfer transaction (1 hbar from operator to recipient)
const transfer = new TransferTransaction()
  .addHbarTransfer(operatorAccount, new Hbar(-1)) // debit operator
  .addHbarTransfer(recipientAccount, new Hbar(1)) // credit recipient
  .setTransactionMemo("invoice 42")
  .setNodeAccountIds([AccountId.fromString("0.0.3")])
  .setTransactionId(txId)
  .freeze();

// Sign the transaction offline
transfer.sign(operatorKey);

// Serialize to bytes and output as hex string
const bytes = transfer.toBytes();
const hex = Buffer.from(bytes).toString("hex");
console.log(hex);
