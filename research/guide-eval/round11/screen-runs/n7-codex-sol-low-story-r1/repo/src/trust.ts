import type { PollarClient } from '@pollar/core';
import { USDC } from './pollar';

/** Lets the wallet hold USDC; sponsorship follows the app's Pollar setting. */
export async function enableUsdc(client: PollarClient): Promise<boolean> {
  const outcome = await client.setTrustline(USDC);
  return outcome.status === 'success';
}
