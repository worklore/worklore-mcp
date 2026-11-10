import {
    AccountId,
    PrivateKey,
    TransferTransaction,
    Timestamp,
    TransactionId,
    Hbar,
    Client,
} from "@hiero-ledger/sdk";
import * as dotenv from "dotenv";

dotenv.config();

// Helper to build a signed transaction and output the raw bytes as hex.
async function main() {
    // Load required environment variables.
    const operatorId = AccountId.fromString(process.env.OPERATOR_ID!);
    const operatorKey = PrivateKey.fromStringDer(process.env.OPERATOR_KEY!);
    const recipientId = AccountId.fromString(process.env.RECIPIENT_ID!);
    const validStartSec = Number(process.env.VALID_START!);

    // Construct the explicit transaction ID with the given valid start time.
    const validStart = new Timestamp(validStartSec, 0);
    const txId = TransactionId.withValidStart(operatorId, validStart);

    // Configure a minimal client. Network details are irrelevant for offline use
    // but the SDK requires a client instance for operator handling.
    const client = new Client({ network: { "0.0.3": "127.0.0.1:50211" } });
    client.setOperator(operatorId, operatorKey);

    // Build the transfer transaction.
    const transaction = new TransferTransaction()
        .addHbarTransfer(operatorId, new Hbar(-1))
        .addHbarTransfer(recipientId, new Hbar(1))
        .setTransactionMemo("invoice 42")
        .setTransactionId(txId)
        // Direct the transaction to node 0.0.3.
        .setNodeAccountIds([AccountId.fromString("0.0.3")]);

    // Freeze the transaction, sign it, then obtain the signed bytes.
    transaction.freeze();
    await transaction.sign(operatorKey);
    const signedBytes = transaction.toBytes();

    // Print the signed transaction bytes as a hex string.
    console.log(Buffer.from(signedBytes).toString("hex"));
}

main().catch((err) => {
    console.error(err);
    process.exit(1);
});

