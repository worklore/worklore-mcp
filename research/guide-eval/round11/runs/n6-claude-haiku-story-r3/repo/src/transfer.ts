import { config } from "dotenv";
import {
  AccountId,
  Hbar,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from "@hiero-ledger/sdk";

// quiet: dotenv 17 otherwise prints a banner to stdout, which would corrupt the output.
config({ quiet: true });

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable ${name}`);
  }
  return value;
}

const operatorId = AccountId.fromString(requireEnv("OPERATOR_ID"));
const operatorKey = PrivateKey.fromStringDer(requireEnv("OPERATOR_KEY"));
const recipientId = AccountId.fromString(requireEnv("RECIPIENT_ID"));

const validStartSeconds = requireEnv("VALID_START");
if (!/^\d+$/.test(validStartSeconds)) {
  throw new Error(`VALID_START must be Unix seconds, got "${validStartSeconds}"`);
}
const validStart = new Timestamp(Number(validStartSeconds), 0);

const nodeId = AccountId.fromString("0.0.3");

// Built and signed entirely offline: no Client, so nothing is submitted to a network.
const transaction = new TransferTransaction()
  .addHbarTransfer(operatorId, new Hbar(-1))
  .addHbarTransfer(recipientId, new Hbar(1))
  .setTransactionMemo("invoice 42")
  .setNodeAccountIds([nodeId])
  .setTransactionId(TransactionId.withValidStart(operatorId, validStart))
  .freezeWith(null);

await transaction.sign(operatorKey);

const bytes = await transaction.toBytesAsync();
process.stdout.write(Buffer.from(bytes).toString("hex") + "\n");
