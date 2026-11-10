// Transfer script using Hedera SDK (offline signing)
import { config } from "dotenv";
config();

import {
  AccountId,
  PrivateKey,
  TransferTransaction,
  TransactionId,
  Hbar,
  Timestamp,
} from "@hiero-ledger/sdk";

// Load environment variables
const OPERATOR_ID = process.env.OPERATOR_ID?.trim();
const OPERATOR_KEY = process.env.OPERATOR_KEY?.trim(); // DER-encoded hex string
const RECIPIENT_ID = process.env.RECIPIENT_ID?.trim();
const VALID_START = process.env.VALID_START?.trim();

if (!OPERATOR_ID || !OPERATOR_KEY || !RECIPIENT_ID || !VALID_START) {
  console.error("Missing required environment variables.");
  process.exit(1);
}

const operatorId = AccountId.fromString(OPERATOR_ID);
const operatorKey = PrivateKey.fromStringDer(OPERATOR_KEY);
const recipientId = AccountId.fromString(RECIPIENT_ID);
const validStartSeconds = Number(VALID_START);
if (isNaN(validStartSeconds)) {
  console.error("VALID_START must be a numeric Unix timestamp.");
  process.exit(1);
}
const validStartDate = new Date(validStartSeconds * 1000);

// Build transaction ID with custom valid start
const txId = TransactionId.withValidStart(operatorId, new Timestamp(validStartSeconds, 0));

// Build the transfer transaction (offline, node 0.0.3)
(async () => {
  const tx = new TransferTransaction()
    .setNodeAccountIds([new AccountId(0, 0, 3)])
    .setTransactionId(txId)
    .addHbarTransfer(operatorId, new Hbar(-1)) // debit operator
    .addHbarTransfer(recipientId, new Hbar(1)) // credit recipient
    .setTransactionMemo("invoice 42")
    .freeze();

  // Sign the transaction
  const signedTx = await tx.sign(operatorKey);

  // Output signed transaction bytes as hex
  const signedBytesHex = Buffer.from(signedTx.toBytes()).toString("hex");
  console.log(signedBytesHex);
})();