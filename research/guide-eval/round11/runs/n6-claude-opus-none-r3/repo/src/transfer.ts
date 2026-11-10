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

// dotenv v17 prints a banner to stdout by default; keep stdout to the hex only.
config({ quiet: true });

function requireEnv(name: string): string {
  const value = process.env[name]?.trim();
  if (!value) throw new Error(`Missing required environment variable ${name}`);
  return value;
}

const operatorId = AccountId.fromString(requireEnv("OPERATOR_ID"));
const recipientId = AccountId.fromString(requireEnv("RECIPIENT_ID"));

const operatorKey = PrivateKey.fromStringDer(requireEnv("OPERATOR_KEY"));
if (operatorKey.type !== "ED25519") {
  throw new Error(`OPERATOR_KEY must be an ED25519 key, got ${operatorKey.type}`);
}

const validStartRaw = requireEnv("VALID_START");
if (!/^\d+$/.test(validStartRaw)) {
  throw new Error("VALID_START must be an integer number of Unix seconds");
}
const validStart = new Timestamp(Number(validStartRaw), 0);

const amount = new Hbar(1);

const tx = new TransferTransaction()
  .addHbarTransfer(operatorId, amount.negated())
  .addHbarTransfer(recipientId, amount)
  .setTransactionMemo(`${TREASURY_MEMO_PREFIX} 42`)
  .setTransactionId(TransactionId.withValidStart(operatorId, validStart))
  .setNodeAccountIds([AccountId.fromString("0.0.3")])
  // No client: freezing offline requires the transaction ID and node IDs above.
  .freeze();

const signed = await tx.sign(operatorKey);

process.stdout.write(Buffer.from(signed.toBytes()).toString("hex") + "\n");
