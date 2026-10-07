/**
 * Evidence Engine
 * 
 * Captures, persists and verifies geospatial evidence with SHA-256 integrity hash.
 * Uses IndexedDB for local structured storage.
 * 
 * License: MIT
 */

import type { GeoEntity } from '../sources/types';

export type EvidenceStatus = 'captured' | 'verified' | 'rejected' | 'pending' | 'superseded';

export interface Evidence {
  id: string;
  missionId?: string;
  sourceId: string;
  entityId: string;
  entityType: string;
  capturedAt: string;
  sourceTimestamp: string;
  coordinates: {
    latitude: number;
    longitude: number;
    altitude?: number;
  };
  sourceUrl?: string;
  sourceType: string;
  metadata: Record<string, any>;
  confidence?: number;
  status: EvidenceStatus;
  hash: string;
  snapshot: string; // JSON string of the entity at capture time
}

const DB_NAME = 'god-eye-sae-evidence';
const DB_VERSION = 1;
const STORE_NAME = 'evidence';

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
        store.createIndex('sourceId', 'sourceId', { unique: false });
        store.createIndex('entityId', 'entityId', { unique: false });
        store.createIndex('capturedAt', 'capturedAt', { unique: false });
        store.createIndex('status', 'status', { unique: false });
      }
    };
  });
}

/**
 * Compute SHA-256 hash using Web Crypto API
 * Hash is computed over a canonical JSON representation of the evidence content
 */
export async function computeHash(content: any): Promise<string> {
  const canonical = JSON.stringify(content, Object.keys(content).sort());
  const encoder = new TextEncoder();
  const data = encoder.encode(canonical);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

/**
 * Capture evidence from a GeoEntity
 */
export async function captureEvidence(
  entity: GeoEntity,
  missionId?: string
): Promise<Evidence> {
  const now = new Date().toISOString();
  
  // Build the content to hash (canonical representation)
  const hashContent = {
    sourceId: entity.sourceId,
    entityId: entity.id,
    entityType: entity.type,
    sourceTimestamp: entity.timestamp,
    coordinates: entity.position,
    sourceUrl: entity.provenance.sourceUrl,
    sourceType: entity.provenance.sourceId,
    metadata: entity.properties,
    snapshot: JSON.stringify(entity),
  };
  
  const hash = await computeHash(hashContent);
  
  const evidence: Evidence = {
    id: `ev_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    missionId,
    sourceId: entity.sourceId,
    entityId: entity.id,
    entityType: entity.type,
    capturedAt: now,
    sourceTimestamp: entity.timestamp,
    coordinates: {
      latitude: entity.position.latitude,
      longitude: entity.position.longitude,
      altitude: entity.position.altitude,
    },
    sourceUrl: entity.provenance.sourceUrl,
    sourceType: entity.provenance.sourceId,
    metadata: entity.properties,
    confidence: undefined,
    status: 'captured',
    hash,
    snapshot: JSON.stringify(entity),
  };
  
  await saveEvidence(evidence);
  return evidence;
}

/**
 * Save evidence to IndexedDB
 */
export async function saveEvidence(evidence: Evidence): Promise<void> {
  const db = await getDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const request = store.put(evidence);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}

/**
 * Get evidence by ID
 */
export async function getEvidence(id: string): Promise<Evidence | undefined> {
  const db = await getDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const store = tx.objectStore(STORE_NAME);
    const request = store.get(id);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
  });
}

/**
 * List all evidence
 */
export async function listEvidence(): Promise<Evidence[]> {
  const db = await getDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const store = tx.objectStore(STORE_NAME);
    const request = store.getAll();
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
  });
}

/**
 * List evidence by source
 */
export async function listEvidenceBySource(sourceId: string): Promise<Evidence[]> {
  const db = await getDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const store = tx.objectStore(STORE_NAME);
    const index = store.index('sourceId');
    const request = index.getAll(sourceId);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
  });
}

/**
 * Verify evidence hash integrity
 */
export async function verifyEvidence(evidence: Evidence): Promise<boolean> {
  const snapshot = JSON.parse(evidence.snapshot);
  const hashContent = {
    sourceId: evidence.sourceId,
    entityId: evidence.entityId,
    entityType: evidence.entityType,
    sourceTimestamp: evidence.sourceTimestamp,
    coordinates: evidence.coordinates,
    sourceUrl: evidence.sourceUrl,
    sourceType: evidence.sourceType,
    metadata: evidence.metadata,
    snapshot: evidence.snapshot,
  };
  const computedHash = await computeHash(hashContent);
  return computedHash === evidence.hash;
}

/**
 * Update evidence status
 */
export async function updateEvidenceStatus(
  id: string,
  status: EvidenceStatus
): Promise<void> {
  const evidence = await getEvidence(id);
  if (!evidence) throw new Error(`Evidence ${id} not found`);
  evidence.status = status;
  await saveEvidence(evidence);
}

/**
 * Delete evidence
 */
export async function deleteEvidence(id: string): Promise<void> {
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
 * Export evidence as JSON
 */
export async function exportEvidenceJSON(): Promise<string> {
  const all = await listEvidence();
  return JSON.stringify({
    exportedAt: new Date().toISOString(),
    version: '1.0',
    count: all.length,
    evidence: all,
  }, null, 2);
}
