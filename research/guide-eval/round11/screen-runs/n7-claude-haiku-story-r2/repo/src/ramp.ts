import type { PollarClient } from '@pollar/core';
import { USDC } from './pollar';

/**
 * "Add money": the best rate for topping up the wallet with Argentine pesos, as pesos per USDC,
 * or null if no route quotes. 0.12 quotes a route (fiat + rail + asset), so the rail comes from
 * the app's available ramp routes rather than being hard-coded.
 */
export async function bestTopUpRate(client: PollarClient, pesos: number): Promise<number | null> {
  const { routes } = await client.getRampRoutes('ONRAMP');
  const route = routes.find(
    (r) => r.fiat.currency === 'ARS' && r.fiat.country === 'AR' && r.asset.code === USDC.code && r.asset.chain === 'STELLAR',
  );
  if (!route) return null;

  const { quotes } = await client.quoteRamp({
    direction: 'ONRAMP',
    fiat: { currency: route.fiat.currency, country: route.fiat.country, rail: route.fiat.rail },
    asset: { code: route.asset.code, identifier: route.asset.identifier, chain: route.asset.chain },
    amount: { value: String(pesos), denomination: 'in' },
  });
  const best = quotes[0];
  if (!best) return null;

  // quotes come best first; the rate is what the user pays per USDC received.
  const received = Number(best.amountOut);
  return received > 0 ? Number(best.amountIn) / received : null;
}
