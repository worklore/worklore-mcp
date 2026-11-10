// Transfer a single hbar from operator to recipient offline and print signed transaction bytes as hex

import { AccountId, PrivateKey, TransactionId, TransferTransaction, Hbar, Timestamp } from "@hashgraph/sdk";
import dotenv from "dotenv";

dotenv.config();

async function main() {
    const operatorIdStr = process.env.OPERATOR_ID;
    const operatorKeyStr = process.env.OPERATOR_KEY;
    const recipientIdStr = process.env.RECIPIENT_ID;
    const validStartStr = process.env.VALID_START;

    if (!operatorIdStr || !operatorKeyStr || !recipientIdStr || !validStartStr) {
        throw new Error("Missing required environment variables");
    }

    const operatorId = AccountId.fromString(operatorIdStr);
    const operatorKey = PrivateKey.fromStringDer(operatorKeyStr);
    const recipientId = AccountId.fromString(recipientIdStr);
    const validStart = Number(validStartStr);

    // Create a TransactionId with explicit valid start timestamp
    const transactionId = TransactionId.withValidStart(operatorId, new Timestamp(validStart, 0));

    const tx = new TransferTransaction()
        .setTransactionId(transactionId)
        .addHbarTransfer(operatorId, new Hbar(-1)) // send 1 hbar
        .addHbarTransfer(recipientId, new Hbar(1))
        .setNodeAccountIds([new AccountId(0, 0, 3)])
        .setTransactionMemo("invoice 42");

    // Freeze the transaction for signing (offline, no client needed)
    tx.freeze();
    // Sign with operator key (await because sign returns a Promise)
    const signedTx = await tx.sign(operatorKey);

    const bytes = signedTx.toBytes();
    const hex = Buffer.from(bytes).toString("hex");
    console.log(hex);
}

main();
