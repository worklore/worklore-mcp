import {
    AccountId,
    Hbar,
    HbarUnit,
    PrivateKey,
    Timestamp,
    TransactionId,
    TransferTransaction,
} from "@hashgraph/sdk";
import dotenv from "dotenv";

// Load environment variables from .env file.
dotenv.config();

const {
    OPERATOR_ID,
    OPERATOR_KEY,
    RECIPIENT_ID,
    VALID_START,
} = process.env;

if (!OPERATOR_ID || !OPERATOR_KEY || !RECIPIENT_ID || !VALID_START) {
    throw new Error("Missing required environment variables.");
}

// Parse identifiers and key.
const operatorId = AccountId.fromString(OPERATOR_ID);
const recipientId = AccountId.fromString(RECIPIENT_ID);
const operatorKey = PrivateKey.fromStringDer(OPERATOR_KEY);

// Build a custom valid start timestamp (seconds, nanos = 0).
const validStartSec = Number(VALID_START);
if (Number.isNaN(validStartSec)) {
    throw new Error("VALID_START must be a numeric Unix timestamp.");
}
const validStart = new Timestamp(validStartSec, 0);

// Create a TransactionId with the explicit valid start.
const txnId = new TransactionId(operatorId, validStart);

// Assemble the transfer transaction (offline).
const transaction = new TransferTransaction()
    .setTransactionId(txnId)
    .setNodeAccountIds([AccountId.fromString("0.0.3")])
    .setTransactionMemo("invoice 42")
    .addHbarTransfer(operatorId, Hbar.from(-1, HbarUnit.Hbar)) // send 1 hbar
    .addHbarTransfer(recipientId, Hbar.from(1, HbarUnit.Hbar)) // receive 1 hbar
    .freeze();

// Sign the transaction with the operator's private key.
const signedTx = await transaction.sign(operatorKey);

// Output the signed transaction bytes as a hex string.
const hex = Buffer.from(signedTx.toBytes()).toString("hex");
console.log(hex);
