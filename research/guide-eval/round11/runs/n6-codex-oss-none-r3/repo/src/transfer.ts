import { config } from "dotenv";
import {
  AccountId,
  PrivateKey,
  TransferTransaction,
  Hbar,
  TransactionId,
  Timestamp,
} from "@hashgraph/sdk";

// Load environment variables from .env (if present)
config();

function requiredEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable ${name}`);
  }
  return value;
}

// Parse required values
const operatorId = AccountId.fromString(requiredEnv("OPERATOR_ID"));
// The SDK provides `fromStringDer` for DER‑encoded hex strings.
const operatorKey = PrivateKey.fromStringDer(requiredEnv("OPERATOR_KEY"));
const recipientId = AccountId.fromString(requiredEnv("RECIPIENT_ID"));
const validStartSec = Number(requiredEnv("VALID_START"));

// Build a Timestamp from the provided Unix seconds
const validStart = Timestamp.fromDate(new Date(validStartSec * 1000));
// Construct a TransactionId with the custom valid start
const txId = new TransactionId(operatorId, validStart);

// Create the transfer transaction (offline, no network calls)
const tx = new TransferTransaction()
  .setTransactionId(txId)
  .setNodeAccountIds([new AccountId(0, 0, 3)])
  .addHbarTransfer(operatorId, new Hbar(-1)) // debit operator
  .addHbarTransfer(recipientId, new Hbar(1)) // credit recipient
  .setTransactionMemo("invoice 42");

// Sign the transaction with the operator's private key
tx.sign(operatorKey);

// Serialize to bytes and output as hex string
const bytes = tx.toBytes();
console.log(Buffer.from(bytes).toString("hex"));
