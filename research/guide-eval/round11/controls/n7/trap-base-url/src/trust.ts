import type { PollarClient } from '@pollar/core';
import { USDC } from './pollar';

/** Lets the wallet hold USDC; the app's sponsorship setting decides who pays the reserve. */
export async function enableUsdc(client: PollarClient): Promise<boolean> {
  const outcome = await client.setTrustline(USDC);
  return outcome.status === 'success';
}
