import type { PollarClient } from '@pollar/core';
import { USDC } from './pollar';

/** Lets the wallet hold USDC; the app sponsors the reserve. */
export async function enableUsdc(client: PollarClient): Promise<boolean> {
  const outcome = await client.setTrustline(USDC, { sponsored: true });
  return outcome.status === 'success';
}
