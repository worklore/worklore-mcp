import type { PollarClient } from '@pollar/core';
import { USDC } from './pollar';

/** Lets the wallet hold USDC. Who pays the reserve is set by the app's sponsorship config, not per call. */
export async function enableUsdc(client: PollarClient): Promise<boolean> {
  const outcome = await client.setTrustline(USDC);
  return outcome.status === 'success';
}
