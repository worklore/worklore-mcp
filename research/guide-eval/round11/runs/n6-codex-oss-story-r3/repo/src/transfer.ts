import "dotenv/config";
import {
  AccountId,
  TransferTransaction,
  Hbar,
  PrivateKey,
  TransactionId,
  Timestamp,
} from "@hiero-ledger/sdk";

/**
 * Build and sign an HBAR transfer transaction offline.
 * The signed transaction bytes are printed as a hex string.
 */
function main() {
  const operatorId = AccountId.fromString(process.env.OPERATOR_ID ?? "");
  const operatorKeyHex = process.env.OPERATOR_KEY ?? "";
  const recipientId = AccountId.fromString(process.env.RECIPIENT_ID ?? "");
  const validStartSec = Number(process.env.VALID_START ?? "0");

  if (!operatorId || !operatorKeyHex || !recipientId || !validStartSec) {
    throw new Error("Missing required environment variables");
  }

  const operatorKey = PrivateKey.fromStringDer(operatorKeyHex);
  // Convert the Unix seconds to a Hedera Timestamp.
  const validStart = Timestamp.fromDate(validStartSec * 1000);
  const txId = TransactionId.withValidStart(operatorId, validStart);

  const transaction = new TransferTransaction()
    .setTransactionId(txId)
    .setNodeAccountIds([new AccountId(0, 0, 3)])
    .addHbarTransfer(operatorId, new Hbar(-1)) // debit operator
    .addHbarTransfer(recipientId, new Hbar(1)) // credit recipient
    .setTransactionMemo("invoice 42");

  // Freeze transaction to prepare for signing (offline mode).
  transaction.freeze();
  transaction.sign(operatorKey);

  const bytes = transaction.toBytes();
  const hex = Buffer.from(bytes).toString("hex");
  console.log(hex);
}

main();
