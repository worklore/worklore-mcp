import { config } from "dotenv";
import {
    AccountId,
    PrivateKey,
    TransferTransaction,
    Hbar,
    TransactionId,
    Timestamp,
} from "@hiero-ledger/sdk";

config(); // load .env variables

async function main() {
    const operatorIdStr = process.env.OPERATOR_ID;
    const operatorKeyStr = process.env.OPERATOR_KEY;
    const recipientIdStr = process.env.RECIPIENT_ID;
    const validStartStr = process.env.VALID_START;

    if (!operatorIdStr || !operatorKeyStr || !recipientIdStr || !validStartStr) {
        console.error("Missing required environment variables");
        process.exit(1);
    }

    const operatorId = AccountId.fromString(operatorIdStr);
    const operatorKey = PrivateKey.fromStringDer(operatorKeyStr);
    const recipientId = AccountId.fromString(recipientIdStr);
    const validStart = Number(validStartStr);

    // Build a Timestamp with the given valid start (seconds) and then a TransactionId
    const timestamp = Timestamp.fromDate(new Date(validStart * 1000));
    const transactionId = TransactionId.withValidStart(operatorId, timestamp);

    const tx = new TransferTransaction()
        .setTransactionId(transactionId)
        .setNodeAccountIds([new AccountId(0, 0, 3)]) // node 0.0.3
        .addHbarTransfer(operatorId, new Hbar(-1)) // debit operator
        .addHbarTransfer(recipientId, new Hbar(1)) // credit recipient
        .setTransactionMemo("invoice 42");

    // Freeze and sign the transaction (sign returns a Promise)
    const signedTx = await tx.freeze().sign(operatorKey);

    // Get the signed bytes and print as hex
    const bytes = signedTx.toBytes();
    console.log(Buffer.from(bytes).toString("hex"));
}

main();