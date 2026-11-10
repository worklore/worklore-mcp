import type { PollarClient } from '@pollar/core';
import { USDC } from './pollar';

/**
 * Lets the wallet hold USDC. Sponsorship is on by default in 0.12: the app covers the reserve when
 * its dashboard config allows it, so no flag is passed.
 */
export async function enableUsdc(client: PollarClient): Promise<boolean> {
  const outcome = await client.setTrustline(USDC);
  return outcome.status === 'success';
}
