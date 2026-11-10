import "dotenv/config";
import {
  AccountId,
  Hbar,
  HbarUnit,
  PrivateKey,
  Timestamp,
  TransactionId,
  TransferTransaction,
} from "@hashgraph/sdk";
import { TREASURY_MEMO_PREFIX } from "./index.ts";

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`missing environment variable ${name}`);
  }
  return value;
}

const NODE_ACCOUNT_ID = "0.0.3";
const MEMO = `${TREASURY_MEMO_PREFIX} 42`;

async function main(): Promise<void> {
  const operatorId = AccountId.fromString(requireEnv("OPERATOR_ID"));
  const operatorKey = PrivateKey.fromStringED25519(requireEnv("OPERATOR_KEY"));
  const recipientId = AccountId.fromString(requireEnv("RECIPIENT_ID"));

  const validStartSeconds = Number(requireEnv("VALID_START"));
  if (!Number.isSafeInteger(validStartSeconds) || validStartSeconds < 0) {
    throw new Error("VALID_START must be a non-negative integer (Unix seconds)");
  }
  const validStart = new Timestamp(validStartSeconds, 0);

  const amount = Hbar.from(1, HbarUnit.Hbar);

  const transaction = new TransferTransaction()
    .addHbarTransfer(operatorId, amount.negated())
    .addHbarTransfer(recipientId, amount)
    .setTransactionMemo(MEMO)
    .setNodeAccountIds([AccountId.fromString(NODE_ACCOUNT_ID)])
    .setTransactionId(TransactionId.withValidStart(operatorId, validStart))
    .freeze();

  await transaction.sign(operatorKey);

  console.log(Buffer.from(transaction.toBytes()).toString("hex"));
}

main().catch((err: unknown) => {
  console.error(err instanceof Error ? err.message : err);
  process.exitCode = 1;
});
