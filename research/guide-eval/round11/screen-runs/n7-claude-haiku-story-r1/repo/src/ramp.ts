import type { PollarClient } from '@pollar/core';
import { USDC } from './pollar';

/**
 * "Add money": the best rate for topping up the wallet with Argentine pesos, as ARS per USDC,
 * or null if no provider quotes. The pair (rail, asset identity) comes from the app's ramp routes,
 * so the quote uses whatever Pollar serves for ARS → USDC on Stellar.
 */
export async function bestTopUpRate(client: PollarClient, pesos: number): Promise<number | null> {
  const { routes } = await client.getRampRoutes('ONRAMP');
  const route = routes.find(
    (r) =>
      r.fiat.country === 'AR' &&
      r.fiat.currency === 'ARS' &&
      r.asset.code === USDC.code &&
      r.asset.chain === 'STELLAR',
  );
  if (!route) return null;

  const { quotes } = await client.quoteRamp({
    direction: 'ONRAMP',
    fiat: { currency: route.fiat.currency, rail: route.fiat.rail, country: route.fiat.country },
    asset: { code: route.asset.code, identifier: route.asset.identifier, chain: route.asset.chain },
    amount: { value: String(pesos), denomination: 'in' },
  });

  // Quotes come best first. Pesos in divided by USDC out is the rate.
  const best = quotes[0];
  if (!best) return null;
  return Number(best.amountIn) / Number(best.amountOut);
}
