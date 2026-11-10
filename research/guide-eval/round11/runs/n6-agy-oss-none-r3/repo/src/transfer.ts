// src/transfer.ts
// Builds and signs a Hedera transfer transaction offline, then prints the signed transaction bytes as hex.

import { AccountId, PrivateKey, TransferTransaction, TransactionId, Hbar, Client, Timestamp } from "@hashgraph/sdk";
import "dotenv/config";

async function main() {
  // Load environment variables
  const operatorIdStr = process.env.OPERATOR_ID;
  const operatorKeyDerHex = process.env.OPERATOR_KEY;
  const recipientIdStr = process.env.RECIPIENT_ID;
  const validStartStr = process.env.VALID_START;

  if (!operatorIdStr || !operatorKeyDerHex || !recipientIdStr || !validStartStr) {
    throw new Error("Missing required environment variables");
  }

  const operatorId = AccountId.fromString(operatorIdStr);
  const operatorKey = PrivateKey.fromStringDer(operatorKeyDerHex);
  const recipientId = AccountId.fromString(recipientIdStr);
  const validStartSec = Number(validStartStr);
  const validStart = new Date(validStartSec * 1000);

  // Create a TransactionId with the provided valid start timestamp
  const txId = TransactionId.withValidStart(operatorId, Timestamp.fromDate(validStart));

  // Build the transfer transaction (offline)
  const transaction = new TransferTransaction()
    .setTransactionId(txId)
    .addHbarTransfer(operatorId, new Hbar(-1)) // Send 1 hbar
    .addHbarTransfer(recipientId, new Hbar(1)) // Receive 1 hbar
    .setTransactionMemo("invoice 42")
    .setNodeAccountIds([AccountId.fromString("0.0.3")]);

  // Freeze the transaction with an offline client (no network needed)
  const offlineClient = new Client({ network: {} });
  await transaction.freezeWith(offlineClient);

  // Sign the transaction with the operator's private key
  await transaction.sign(operatorKey);

  // Serialize signed transaction bytes and output as hex
  const signedBytes = transaction.toBytes();
  console.log(Buffer.from(signedBytes).toString("hex"));
}

main().catch((err) => {
  console.error("Error:", err);
  process.exit(1);
});
