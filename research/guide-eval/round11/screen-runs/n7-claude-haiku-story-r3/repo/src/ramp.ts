import type { PollarClient } from '@pollar/core';
import { USDC } from './pollar';

/**
 * "Add money": the best rate for topping up the wallet with Argentine pesos, expressed as pesos per USDC,
 * or null if there is no route or no provider quotes.
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
    fiat: { currency: route.fiat.currency, country: route.fiat.country, rail: route.fiat.rail },
    asset: { code: route.asset.code, identifier: route.asset.identifier, chain: route.asset.chain },
    amount: { value: String(pesos), denomination: 'in' },
  });
  const best = quotes[0];
  if (!best) return null;

  // Quotes come best first. Pesos in (amountIn) divided by USDC out (amountOut) is pesos per USDC.
  const rate = Number(best.amountIn) / Number(best.amountOut);
  return Number.isFinite(rate) ? rate : null;
}
