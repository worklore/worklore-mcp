import type { PollarClient } from '@pollar/core';
import { USDC } from './pollar';

/**
 * Lets the wallet hold USDC; the app sponsors the reserve. Sponsorship is on by default in
 * Pollar 0.12 (the app covers the reserve when eligible), so no option is needed.
 */
export async function enableUsdc(client: PollarClient): Promise<boolean> {
  const outcome = await client.setTrustline(USDC);
  return outcome.status === 'success';
}
