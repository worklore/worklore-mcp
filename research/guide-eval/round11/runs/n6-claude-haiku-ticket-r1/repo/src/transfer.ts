import "dotenv/config";
import {
    AccountId,
    Hbar,
    HbarUnit,
    PrivateKey,
    Timestamp,
    TransactionId,
    TransferTransaction,
} from "@hiero-ledger/sdk";

function required(name: string): string {
    const value = process.env[name];
    if (!value) {
        throw new Error(`Missing environment variable ${name}`);
    }
    return value;
}

function parseUnixSeconds(name: string): number {
    const raw = required(name);
    if (!/^\d+$/.test(raw)) {
        throw new Error(`${name} must be a Unix timestamp in whole seconds, got "${raw}"`);
    }
    return Number(raw);
}

async function main(): Promise<void> {
    const operatorId = AccountId.fromString(required("OPERATOR_ID"));
    const operatorKey = PrivateKey.fromStringDer(required("OPERATOR_KEY"));
    const recipientId = AccountId.fromString(required("RECIPIENT_ID"));
    const validStart = new Timestamp(parseUnixSeconds("VALID_START"), 0);
    const nodeId = AccountId.fromString("0.0.3");

    const transaction = new TransferTransaction()
        .addHbarTransfer(operatorId, Hbar.from(-1, HbarUnit.Hbar))
        .addHbarTransfer(recipientId, Hbar.from(1, HbarUnit.Hbar))
        .setTransactionMemo("invoice 42")
        .setTransactionId(TransactionId.withValidStart(operatorId, validStart))
        .setNodeAccountIds([nodeId])
        .freezeWith(null);

    const signed = await transaction.sign(operatorKey);
    const bytes = await signed.toBytesAsync();

    // Only the hex bytes go to stdout; everything else goes to stderr.
    console.log(Buffer.from(bytes).toString("hex"));
}

main().catch((error: unknown) => {
    console.error(error instanceof Error ? error.message : error);
    process.exit(1);
});
