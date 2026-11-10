import type { PollarClient } from '@pollar/core';
import { USDC } from './pollar';

/** "Add money": the best rate for topping up the wallet with Argentine pesos, or null if no provider quotes. */
export async function bestTopUpRate(client: PollarClient, pesos: number): Promise<number | null> {
  const { routes } = await client.getRampRoutes('ONRAMP');
  const matching = routes.filter(({ fiat, asset }) =>
    fiat.country === 'AR' && fiat.currency === 'ARS' &&
    asset.chain === 'STELLAR' && asset.code === USDC.code && asset.identifier === USDC.issuer
  );
  const quotes = await Promise.all(matching.map(({ fiat, asset }) => client.quoteRamp({
    direction: 'ONRAMP', fiat, asset,
    amount: { value: String(pesos), denomination: 'in' },
  })));
  const rates = quotes.flatMap(({ quotes }) => quotes.map(({ amountIn, amountOut }) => {
    const received = Number(amountOut);
    return received > 0 ? Number(amountIn) / received : Infinity;
  })).filter(Number.isFinite);
  return rates.length ? Math.min(...rates) : null;
}
