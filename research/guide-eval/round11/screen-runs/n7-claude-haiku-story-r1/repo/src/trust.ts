import type { PollarClient } from '@pollar/core';
import { USDC } from './pollar';

/**
 * Lets the wallet hold USDC. Pollar decides who pays the reserve from the app's own sponsorship
 * setting, so no per-call option is passed. The app's sponsorship must stay on to keep it sponsored.
 */
export async function enableUsdc(client: PollarClient): Promise<boolean> {
  const outcome = await client.setTrustline(USDC);
  return outcome.status === 'success';
}
