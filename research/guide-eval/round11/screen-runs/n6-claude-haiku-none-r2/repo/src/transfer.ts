import "dotenv/config";
import {
    AccountId,
    Hbar,
    PrivateKey,
    Timestamp,
    TransactionId,
    TransferTransaction,
} from "@hashgraph/sdk";

function required(name: string): string {
    const value = process.env[name];
    if (!value) {
        throw new Error(`Missing environment variable ${name}`);
    }
    return value;
}

const operatorId = AccountId.fromString(required("OPERATOR_ID"));
const operatorKey = PrivateKey.fromStringDer(required("OPERATOR_KEY"));
const recipientId = AccountId.fromString(required("RECIPIENT_ID"));

const validStartSeconds = Number(required("VALID_START"));
if (!Number.isSafeInteger(validStartSeconds) || validStartSeconds < 0) {
    throw new Error(`VALID_START must be a Unix timestamp in seconds, got "${process.env.VALID_START}"`);
}

const nodeAccountId = AccountId.fromString("0.0.3");

const transactionId = TransactionId.withValidStart(
    operatorId,
    new Timestamp(validStartSeconds, 0),
);

const transaction = new TransferTransaction()
    .setTransactionId(transactionId)
    .setNodeAccountIds([nodeAccountId])
    .setTransactionMemo("invoice 42")
    .addHbarTransfer(operatorId, new Hbar(-1))
    .addHbarTransfer(recipientId, new Hbar(1))
    .freeze();

const signed = await transaction.sign(operatorKey);

console.log(Buffer.from(signed.toBytes()).toString("hex"));
