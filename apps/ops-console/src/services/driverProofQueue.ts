const DB_NAME = 'freightpilot-driver-proofs';
const DB_VERSION = 1;
const STORE = 'proofs';

export type QueuedProof = {
  id: string;
  scope: string;
  orderId: string;
  fileName: string;
  contentType: string;
  recipientName?: string;
  notes?: string;
  queuedAt: number;
  blob: Blob;
};

let dbPromise: Promise<IDBDatabase> | null = null;
let lastQueuedAt = 0;

function requestResult<T>(request: IDBRequest<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error ?? new Error('IndexedDB request failed'));
  });
}

function openDatabase(): Promise<IDBDatabase> {
  if (typeof indexedDB === 'undefined') {
    return Promise.reject(new Error('Offline proof storage is unavailable'));
  }
  if (dbPromise) return dbPromise;
  dbPromise = new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE)) {
        const store = db.createObjectStore(STORE, { keyPath: 'id' });
        store.createIndex('scope', 'scope', { unique: false });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error ?? new Error('Could not open proof storage'));
  });
  return dbPromise;
}

export async function queueDriverProof(input: {
  scope: string;
  orderId: string;
  file: Blob;
  fileName: string;
  recipientName?: string;
  notes?: string;
}): Promise<QueuedProof> {
  const queuedAt = Math.max(Date.now(), lastQueuedAt + 1);
  lastQueuedAt = queuedAt;
  const id =
    typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
      ? `${input.scope}:${crypto.randomUUID()}`
      : `${input.scope}:${queuedAt}:${Math.random().toString(36).slice(2)}`;
  const row: QueuedProof = {
    id,
    scope: input.scope,
    orderId: input.orderId,
    fileName: input.fileName,
    contentType: input.file.type || 'image/jpeg',
    recipientName: input.recipientName,
    notes: input.notes,
    queuedAt,
    blob: input.file,
  };
  const db = await openDatabase();
  const tx = db.transaction(STORE, 'readwrite');
  tx.objectStore(STORE).put(row);
  await new Promise<void>((resolve, reject) => {
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error ?? new Error('Could not queue proof'));
    tx.onabort = () => reject(tx.error ?? new Error('Could not queue proof'));
  });
  return row;
}

export async function listQueuedProofs(scope: string): Promise<QueuedProof[]> {
  if (typeof indexedDB === 'undefined') return [];
  const db = await openDatabase();
  const tx = db.transaction(STORE, 'readonly');
  const rows = await requestResult(
    tx.objectStore(STORE).index('scope').getAll(IDBKeyRange.only(scope)),
  );
  return (rows as QueuedProof[]).sort((left, right) => left.queuedAt - right.queuedAt);
}

export async function deleteQueuedProof(id: string): Promise<void> {
  if (typeof indexedDB === 'undefined') return;
  const db = await openDatabase();
  const tx = db.transaction(STORE, 'readwrite');
  tx.objectStore(STORE).delete(id);
  await new Promise<void>((resolve, reject) => {
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error ?? new Error('Could not remove proof'));
    tx.onabort = () => reject(tx.error ?? new Error('Could not remove proof'));
  });
}

export async function clearQueuedProofs(scope: string): Promise<void> {
  const rows = await listQueuedProofs(scope);
  await Promise.all(rows.map((row) => deleteQueuedProof(row.id)));
}

export async function clearAllQueuedProofs(): Promise<void> {
  if (typeof indexedDB === 'undefined') return;
  const db = await openDatabase();
  const tx = db.transaction(STORE, 'readwrite');
  tx.objectStore(STORE).clear();
  await new Promise<void>((resolve, reject) => {
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error ?? new Error('Could not clear proof storage'));
    tx.onabort = () => reject(tx.error ?? new Error('Could not clear proof storage'));
  });
}

export async function pruneOtherProofScopes(scope: string): Promise<void> {
  if (typeof indexedDB === 'undefined') return;
  const db = await openDatabase();
  const tx = db.transaction(STORE, 'readonly');
  const rows = (await requestResult(tx.objectStore(STORE).getAll())) as QueuedProof[];
  const staleIds = rows.filter((row) => row.scope !== scope).map((row) => row.id);
  await Promise.all(staleIds.map((id) => deleteQueuedProof(id)));
}
