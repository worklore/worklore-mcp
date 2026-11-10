import { config } from "dotenv";
import {
    AccountId,
    PrivateKey,
    TransactionId,
    Timestamp,
    TransferTransaction,
    Hbar,
} from "@hiero-ledger/sdk";

config();

const operatorIdStr = process.env.OPERATOR_ID;
const operatorKeyHex = process.env.OPERATOR_KEY;
const recipientIdStr = process.env.RECIPIENT_ID;
const validStartStr = process.env.VALID_START;

if (!operatorIdStr || !operatorKeyHex || !recipientIdStr || !validStartStr) {
    throw new Error("Missing required environment variables");
}

const operatorId = AccountId.fromString(operatorIdStr);
const operatorKey = PrivateKey.fromStringDer(operatorKeyHex);
const recipientId = AccountId.fromString(recipientIdStr);
const validStartSec = Number(validStartStr);
const timestamp = Timestamp.fromDate(new Date(validStartSec * 1000));

const transactionId = TransactionId.withValidStart(operatorId, timestamp);

(async () => {
    const tx = await new TransferTransaction()
        .setTransactionId(transactionId)
    .setNodeAccountIds([AccountId.fromString('0.0.3')])
        .addHbarTransfer(operatorId, new Hbar(-1))
        .addHbarTransfer(recipientId, new Hbar(1))
        .setTransactionMemo("invoice 42")
        .freeze();

    const signedTx = await tx.sign(operatorKey);
    const bytes = signedTx.toBytes();
    console.log(Buffer.from(bytes).toString("hex"));
})();
