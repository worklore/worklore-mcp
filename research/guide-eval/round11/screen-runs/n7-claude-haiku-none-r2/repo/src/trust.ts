import type { PollarClient } from '@pollar/core';
import { USDC } from './pollar';

/**
 * Lets the wallet hold USDC; the app sponsors the reserve.
 * Sponsorship is on by default in 0.12 (the app's dashboard config decides), so no option is passed.
 */
export async function enableUsdc(client: PollarClient): Promise<boolean> {
  const outcome = await client.setTrustline(USDC);
  return outcome.status === 'success';
}
