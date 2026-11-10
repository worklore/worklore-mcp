import { config } from "dotenv";
import {
    AccountId,
    PrivateKey,
    TransactionId,
    TransferTransaction,
    Hbar,
    Timestamp,
} from "@hiero-ledger/sdk";

// Load environment variables from .env (if present).
config();

/**
 * Build, sign, and output a signed transfer transaction.
 * The transaction is constructed entirely offline – no client or network is required.
 */
async function main(): Promise<void> {
    // Required environment variables.
    const operatorIdStr = process.env.OPERATOR_ID;
    const operatorKeyDer = process.env.OPERATOR_KEY;
    const recipientIdStr = process.env.RECIPIENT_ID;
    const validStartStr = process.env.VALID_START;

    if (!operatorIdStr || !operatorKeyDer || !recipientIdStr || !validStartStr) {
        throw new Error("Missing required environment variables");
    }

    const operatorId = AccountId.fromString(operatorIdStr);
    const operatorKey = PrivateKey.fromStringDer(operatorKeyDer);
    const recipientId = AccountId.fromString(recipientIdStr);
    const validStartSec = Number(validStartStr);
    if (Number.isNaN(validStartSec)) {
        throw new Error("VALID_START must be a number representing Unix seconds");
    }
    const validStart = new Timestamp(validStartSec, 0);

    // Transaction ID with explicit valid start.
    const txId = TransactionId.withValidStart(operatorId, validStart);

    // Build the transfer transaction.
    const tx = new TransferTransaction()
        .setTransactionId(txId)
        .setNodeAccountIds([new AccountId(0, 0, 3)])
        .addHbarTransfer(operatorId, new Hbar(-1)) // operator pays 1 hbar
        .addHbarTransfer(recipientId, new Hbar(1)) // recipient receives 1 hbar
        .setTransactionMemo("invoice 42")
        .freeze(); // freeze for offline signing

    // Sign with the operator private key.
    await tx.sign(operatorKey);

    // Serialize signed transaction and output as hex.
    const signedBytes = tx.toBytes();
    console.log(Buffer.from(signedBytes).toString("hex"));
}

void main();

