import 'fake-indexeddb/auto';
import { beforeEach, describe, expect, it } from 'vitest';

import {
  clearAllQueuedProofs,
  clearQueuedProofs,
  deleteQueuedProof,
  listQueuedProofs,
  pruneOtherProofScopes,
  queueDriverProof,
} from './driverProofQueue';

const scope = 'driver-scope-a';
const image = new Blob([new Uint8Array([0x89, 0x50, 0x4e, 0x47])], {
  type: 'image/png',
});

beforeEach(async () => {
  await clearQueuedProofs(scope);
  await clearQueuedProofs('driver-scope-b');
});

describe('driver proof queue', () => {
  it('stores proof metadata and the original blob in FIFO order', async () => {
    const first = await queueDriverProof({
      scope,
      orderId: 'order-1',
      file: image,
      fileName: 'delivery.png',
      recipientName: 'Store manager',
    });
    const second = await queueDriverProof({
      scope,
      orderId: 'order-2',
      file: image,
      fileName: 'second.png',
    });

    const rows = await listQueuedProofs(scope);
    expect(rows.map((row) => row.id)).toEqual([first.id, second.id]);
    expect(rows[0].contentType).toBe('image/png');
    expect(rows[0].recipientName).toBe('Store manager');
    expect(rows[0].blob.size).toBe(image.size);
  });

  it('removes a proof after upload and prunes other driver scopes', async () => {
    const first = await queueDriverProof({
      scope,
      orderId: 'order-1',
      file: image,
      fileName: 'delivery.png',
    });
    await queueDriverProof({
      scope: 'driver-scope-b',
      orderId: 'order-2',
      file: image,
      fileName: 'other.png',
    });

    await deleteQueuedProof(first.id);
    expect(await listQueuedProofs(scope)).toEqual([]);

    await pruneOtherProofScopes(scope);
    expect(await listQueuedProofs('driver-scope-b')).toEqual([]);
  });

  it('clears every queued proof on logout', async () => {
    await queueDriverProof({
      scope,
      orderId: 'order-1',
      file: image,
      fileName: 'delivery.png',
    });
    await queueDriverProof({
      scope: 'driver-scope-b',
      orderId: 'order-2',
      file: image,
      fileName: 'other.png',
    });

    await clearAllQueuedProofs();

    expect(await listQueuedProofs(scope)).toEqual([]);
    expect(await listQueuedProofs('driver-scope-b')).toEqual([]);
  });
});
