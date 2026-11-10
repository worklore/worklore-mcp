import { TransferTransaction, PrivateKey } from "@hashgraph/sdk";

const tx = new TransferTransaction();
const key = PrivateKey.generate();

// Test if sign method accepts PrivateKey
tx.freeze();
const signed = await tx.sign(key);
