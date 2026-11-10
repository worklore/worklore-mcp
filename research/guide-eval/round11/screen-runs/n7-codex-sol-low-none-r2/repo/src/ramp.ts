import { isPollarApiError, type PollarClient, type RampQuotesResponse } from '@pollar/core';
import { USDC } from './pollar';

/** "Add money": the best ARS per USDC rate for an ARS top-up, or null when no route quotes. */
export async function bestTopUpRate(client: PollarClient, pesos: number): Promise<number | null> {
  const { routes } = await client.getRampRoutes('ONRAMP');
  const matching = routes.filter((route) =>
    route.fiat.country === 'AR' && route.fiat.currency === 'ARS' &&
    route.asset.chain === 'STELLAR' && route.asset.code === USDC.code &&
    route.asset.identifier === USDC.issuer
  );

  const results = await Promise.all(matching.map(async (route): Promise<RampQuotesResponse | null> => {
    try {
      return await client.quoteRamp({
        direction: 'ONRAMP',
        fiat: { country: route.fiat.country, currency: route.fiat.currency, rail: route.fiat.rail },
        asset: { chain: route.asset.chain, code: route.asset.code, identifier: route.asset.identifier },
        amount: { value: String(pesos), denomination: 'in' },
      });
    } catch (error) {
      if (isPollarApiError(error) && error.code === 'SDK_RAMPS_NO_ROUTE') return null;
      throw error;
    }
  }));

  const rates = results.flatMap((result) => (result?.quotes ?? []).map((quote) => {
    const fiat = Number(quote.amountIn);
    const usdc = Number(quote.amountOut);
    return fiat > 0 && usdc > 0 ? fiat / usdc : null;
  })).filter((rate): rate is number => rate !== null && Number.isFinite(rate));

  return rates.length ? Math.min(...rates) : null;
}
