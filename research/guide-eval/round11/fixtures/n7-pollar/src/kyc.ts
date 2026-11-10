import type { PollarClient } from '@pollar/core';

/** Waits for the identity check and returns the line the wallet screen shows. */
export async function kycMessage(client: PollarClient, providerId: string): Promise<string> {
  const status = await client.pollKycStatus(providerId, { intervalMs: 3000, timeoutMs: 120_000 });
  switch (status) {
    case 'approved':
      return 'Verified';
    case 'rejected':
      return 'Verification failed';
    case 'pending':
      return 'Still being checked';
    case 'none':
      return 'Not started';
  }
}
