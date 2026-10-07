/**
 * Audit Event System
 * 
 * Records significant operations for traceability.
 * Uses IndexedDB for local persistence.
 * 
 * License: MIT
 */

export type AuditAction =
  | 'SOURCE_ENABLED'
  | 'SOURCE_DISABLED'
  | 'SOURCE_FETCH_STARTED'
  | 'SOURCE_FETCH_SUCCEEDED'
  | 'SOURCE_FETCH_FAILED'
  | 'ENTITY_SELECTED'
  | 'EVIDENCE_CAPTURED'
  | 'EVIDENCE_VERIFIED'
  | 'EVIDENCE_EXPORTED'
  | 'MISSION_STARTED'
  | 'MISSION_CHANGED';

export interface AuditEvent {
  id: string;
  timestamp: string;
  actor: 'user' | 'system';
  action: AuditAction;
  resource: string;
  resourceId?: string;
  missionId?: string;
  status: 'success' | 'failure' | 'pending';
  metadata?: Record<string, any>;
}

const DB_NAME = 'god-eye-sae-audit';
const DB_VERSION = 1;
const STORE_NAME = 'audit';
const MAX_EVENTS = 1000; // Keep last 1000 events

let dbInstance: IDBDatabase | null = null;

async function getDB(): Promise<IDBDatabase> {
  if (dbInstance) return dbInstance;
  
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      dbInstance = request.result;
      resolve(dbInstance);
    };
    
    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, { keyPath: 'id' });
        store.createIndex('timestamp', 'timestamp', { unique: false });
        store.createIndex('action', 'action', { unique: false });
        store.createIndex('resource', 'resource', { unique: false });
      }
    };
  });
}

/**
 * Record an audit event
 */
export async function recordAuditEvent(
  action: AuditAction,
  resource: string,
  options: {
    actor?: 'user' | 'system';
    resourceId?: string;
    missionId?: string;
    status?: 'success' | 'failure' | 'pending';
    metadata?: Record<string, any>;
  } = {}
): Promise<AuditEvent> {
  const event: AuditEvent = {
    id: `audit_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    timestamp: new Date().toISOString(),
    actor: options.actor || 'system',
    action,
    resource,
    resourceId: options.resourceId,
    missionId: options.missionId,
    status: options.status || 'success',
    metadata: options.metadata,
  };
  
  const db = await getDB();
  
  // Save event
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const request = store.add(event);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
  
  // Prune old events if over limit
  await pruneOldEvents();
  
  return event;
}

/**
 * Prune old events to keep only the last MAX_EVENTS
 */
async function pruneOldEvents(): Promise<void> {
  const db = await getDB();
  const count = await new Promise<number>((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const store = tx.objectStore(STORE_NAME);
    const request = store.count();
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
  });
  
  if (count <= MAX_EVENTS) return;
  
  const toDelete = count - MAX_EVENTS;
  const events = await listAuditEvents();
  const oldest = events.slice(0, toDelete);
  
  for (const event of oldest) {
    await deleteAuditEvent(event.id);
  }
}

/**
 * List audit events (newest first)
 */
export async function listAuditEvents(limit?: number): Promise<AuditEvent[]> {
  const db = await getDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const store = tx.objectStore(STORE_NAME);
    const index = store.index('timestamp');
    const request = index.getAll();
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const events = request.result.reverse(); // Newest first
      resolve(limit ? events.slice(0, limit) : events);
    };
  });
}

/**
 * Get audit events by action
 */
export async function getAuditEventsByAction(action: AuditAction): Promise<AuditEvent[]> {
  const db = await getDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const store = tx.objectStore(STORE_NAME);
    const index = store.index('action');
    const request = index.getAll(action);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result.reverse());
  });
}

/**
 * Delete audit event
 */
export async function deleteAuditEvent(id: string): Promise<void> {
  const db = await getDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const request = store.delete(id);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}

/**
 * Clear all audit events
 */
export async function clearAuditEvents(): Promise<void> {
  const db = await getDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const request = store.clear();
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}

/**
 * Export audit events as JSON
 */
export async function exportAuditEventsJSON(): Promise<string> {
  const events = await listAuditEvents();
  return JSON.stringify({
    exportedAt: new Date().toISOString(),
    version: '1.0',
    count: events.length,
    events,
  }, null, 2);
}
