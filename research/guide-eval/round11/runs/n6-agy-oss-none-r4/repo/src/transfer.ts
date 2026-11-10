// Transfer HBAR using Hedera JS SDK (offline)
// Run with: npx tsx src/transfer.ts

import { config } from "dotenv";
config(); // load .env variables

import {
  AccountId,
  PrivateKey,
  Hbar,
  TransferTransaction,
  TransactionId,
  Timestamp,
} from "@hashgraph/sdk";

async function main() {
  const operatorIdStr = process.env.OPERATOR_ID;
  const operatorKeyHex = process.env.OPERATOR_KEY;
  const recipientIdStr = process.env.RECIPIENT_ID;
  const validStartStr = process.env.VALID_START;

  if (!operatorIdStr || !operatorKeyHex || !recipientIdStr || !validStartStr) {
    throw new Error("Missing required environment variables");
  }

  const operatorId = AccountId.fromString(operatorIdStr);
  const operatorKey = PrivateKey.fromStringED25519(operatorKeyHex);
  const recipientId = AccountId.fromString(recipientIdStr);
  const validStart = Number(validStartStr);

  // Build custom TransactionId with given valid start timestamp
  const timestamp = new Timestamp(validStart, 0);
  const txId = new TransactionId(operatorId, timestamp);

  const tx = new TransferTransaction()
    .setTransactionId(txId)
    .setNodeAccountIds([new AccountId(0, 0, 3)])
    .setTransactionMemo("invoice 42")
    .addHbarTransfer(operatorId, new Hbar(-1)) // send 1 HBAR
    .addHbarTransfer(recipientId, new Hbar(1));

  // Sign transaction with operator key
  await tx.sign(operatorKey);

  const bytes = tx.toBytes();
  const hex = Buffer.from(bytes).toString("hex");
  console.log(hex);
}

main().catch((err) => {
  console.error("Error:", err);
  process.exit(1);
});
