import type { PollarClient } from '@pollar/core';
import { USDC } from './pollar';

/** "Add money": the best rate for topping up the wallet with Argentine pesos, or null if no provider quotes. */
export async function bestTopUpRate(client: PollarClient, pesos: number): Promise<number | null> {
  const { routes } = await client.getRampRoutes('ONRAMP');
  const matching = routes.filter(({ fiat, asset }) =>
    fiat.country === 'AR' && fiat.currency === 'ARS' &&
    asset.chain === 'STELLAR' && asset.code === USDC.code && asset.identifier === USDC.issuer,
  );
  const results = await Promise.all(matching.map(({ fiat, asset }) => client.quoteRamp({
    direction: 'ONRAMP',
    fiat: { country: fiat.country, currency: fiat.currency, rail: fiat.rail },
    asset: { chain: asset.chain, code: asset.code, identifier: asset.identifier },
    amount: { value: String(pesos), denomination: 'in' },
  })));
  const outputs = results.flatMap(({ quotes }) => quotes.map(({ amountOut }) => Number(amountOut)))
    .filter((amount) => Number.isFinite(amount) && amount > 0);
  return outputs.length ? pesos / Math.max(...outputs) : null;
}
