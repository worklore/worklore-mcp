import type { PollarClient } from '@pollar/core';
import { USDC } from './pollar';

/** Lets the wallet hold USDC; reserve sponsorship follows the app configuration. */
export async function enableUsdc(client: PollarClient): Promise<boolean> {
  const outcome = await client.setTrustline(USDC);
  return outcome.status === 'success';
}
