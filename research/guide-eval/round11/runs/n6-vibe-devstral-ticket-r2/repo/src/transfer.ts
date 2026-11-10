import { TransferTransaction, PrivateKey, TransactionId, AccountId, Hbar, Timestamp } from "@hiero-ledger/sdk";
import * as dotenv from "dotenv";

async function main() {
    dotenv.config();

    const operatorId = process.env.OPERATOR_ID!;
    const operatorKeyHex = process.env.OPERATOR_KEY!;
    const recipientId = process.env.RECIPIENT_ID!;
    const validStartSeconds = parseInt(process.env.VALID_START!);

    const operatorKey = PrivateKey.fromStringDer(operatorKeyHex);
    const operatorAccountId = AccountId.fromString(operatorId);
    const recipientAccountId = AccountId.fromString(recipientId);
    const validStart = new Timestamp(validStartSeconds, 0);

    const transaction = new TransferTransaction()
        .addHbarTransfer(operatorAccountId, new Hbar(-1))
        .addHbarTransfer(recipientAccountId, new Hbar(1))
        .setTransactionMemo("invoice 42")
        .setNodeAccountIds([AccountId.fromString("0.0.3")])
        .setTransactionId(
            TransactionId.withValidStart(
                operatorAccountId,
                validStart
            )
        );

    await transaction.freeze();
    const signedTransaction = await transaction.sign(operatorKey);

    console.log(Buffer.from(signedTransaction.toBytes()).toString("hex"));
}

main();
