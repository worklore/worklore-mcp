import { config } from "dotenv";
import {
  AccountId,
  Hbar,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from "@hiero-ledger/sdk";
import { TREASURY_MEMO_PREFIX } from "./index.ts";

// quiet: dotenv 17 otherwise logs a banner to stdout, which would corrupt the output.
config({ quiet: true });

function requireEnv(name: string): string {
  const value = process.env[name];
  if (value === undefined || value.trim() === "") {
    throw new Error(`Missing required environment variable ${name}`);
  }
  return value.trim();
}

const operatorId = AccountId.fromString(requireEnv("OPERATOR_ID"));
const operatorKey = PrivateKey.fromStringDer(requireEnv("OPERATOR_KEY"));
const recipientId = AccountId.fromString(requireEnv("RECIPIENT_ID"));

const validStartRaw = requireEnv("VALID_START");
if (!/^\d+$/.test(validStartRaw)) {
  throw new Error(`VALID_START must be a whole number of Unix seconds, got "${validStartRaw}"`);
}
const validStart = new Timestamp(Number(validStartRaw), 0);

if (operatorKey.type !== "ED25519") {
  throw new Error(`OPERATOR_KEY must be an ED25519 key, got ${operatorKey.type}`);
}

const amount = new Hbar(1);

const tx = new TransferTransaction()
  .addHbarTransfer(operatorId, amount.negated())
  .addHbarTransfer(recipientId, amount)
  .setTransactionMemo(`${TREASURY_MEMO_PREFIX} 42`)
  .setNodeAccountIds([AccountId.fromString("0.0.3")])
  .setTransactionId(TransactionId.withValidStart(operatorId, validStart))
  .freeze(); // no client: offline freeze, never touches the network

await tx.sign(operatorKey);

process.stdout.write(Buffer.from(tx.toBytes()).toString("hex") + "\n");
