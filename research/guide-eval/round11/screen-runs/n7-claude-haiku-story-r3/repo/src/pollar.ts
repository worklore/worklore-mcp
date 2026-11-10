import type { PollarClientConfig } from '@pollar/core';

export const pollarConfig: PollarClientConfig = {
  apiKey: 'pub_testnet_tipjar_demo',
  stellarNetwork: 'testnet',
  // Origin only: the SDK adds its API version (/v3 in 0.12) itself.
  baseUrl: 'https://sdk.api.pollar.xyz',
};

export const USDC = { code: 'USDC', issuer: 'GBBD47IF6LWK7P7MDEVSCWR7DPUWV3NY3DTQEVFL4NAT4AQH3ZLLFLA5' };
