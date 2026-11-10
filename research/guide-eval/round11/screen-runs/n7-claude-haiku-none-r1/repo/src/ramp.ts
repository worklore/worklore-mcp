import { isPollarApiError, type PollarClient, type RampQuote, type RampRoute } from '@pollar/core';
import { USDC } from './pollar';

/** The ARS -> USDC on-ramp routes (one per payment rail), e.g. the bank transfer rail. */
function arsToUsdcRoutes(routes: RampRoute[]): RampRoute[] {
  return routes.filter(
    (r) =>
      r.fiat.country === 'AR' &&
      r.fiat.currency === 'ARS' &&
      r.asset.code === USDC.code &&
      r.asset.chain === 'STELLAR' &&
      r.asset.identifier === USDC.issuer,
  );
}

/** ARS paid per USDC received, including the fees in the quote. */
function pesosPerUsdc(quote: RampQuote): number | null {
  const out = Number(quote.amountOut);
  return out > 0 ? Number(quote.amountIn) / out : null;
}

/**
 * "Add money": the best rate for topping up the wallet with Argentine pesos, or null if no provider quotes.
 * Quotes every ARS route, then takes the lowest pesos-per-USDC.
 */
export async function bestTopUpRate(client: PollarClient, pesos: number): Promise<number | null> {
  const { routes } = await client.getRampRoutes('ONRAMP');
  const quotes = await Promise.all(
    arsToUsdcRoutes(routes).map(async (route) => {
      try {
        const res = await client.quoteRamp({
          direction: 'ONRAMP',
          fiat: { currency: route.fiat.currency, rail: route.fiat.rail, country: route.fiat.country },
          asset: { code: route.asset.code, identifier: route.asset.identifier, chain: route.asset.chain },
          amount: { value: String(pesos), denomination: 'in' },
        });
        return res.quotes;
      } catch (err) {
        // No route with liquidity answers 422 SDK_RAMPS_NO_ROUTE: that is "no quote" for this rail.
        if (isPollarApiError(err) && err.code === 'SDK_RAMPS_NO_ROUTE') return [];
        throw err;
      }
    }),
  );
  const rates = quotes.flat().map(pesosPerUsdc).filter((r): r is number => r !== null);
  return rates.length > 0 ? Math.min(...rates) : null;
}
