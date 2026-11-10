import type { PollarClient } from '@pollar/core';
import { USDC } from './pollar';

/**
 * Lets the wallet hold USDC. Sponsorship is on by default: the app covers the reserve when eligible,
 * and the app's Pollar settings decide it, so no per-call option is passed.
 */
export async function enableUsdc(client: PollarClient): Promise<boolean> {
  const outcome = await client.setTrustline(USDC);
  return outcome.status === 'success';
}
