/**
 * Source Adapter Infrastructure
 * 
 * Common abstraction for all data sources in GOD EYE SAE.
 * Based on upstream God's Eye View provider pattern.
 * 
 * License: MIT (compatible with upstream)
 */

export type SourceStatus =
  | 'INTEGRATED_VERIFIED'
  | 'INTEGRATED_UNVERIFIED'
  | 'NOT_CONFIGURED'
  | 'UNAVAILABLE'
  | 'ERROR'
  | 'LOADING'
  | 'DISABLED';

export interface GeoEntity {
  id: string;
  sourceId: string;
  type: string;
  subtype?: string;
  name?: string;
  timestamp: string;
  position: {
    longitude: number;
    latitude: number;
    altitude?: number;
  };
  heading?: number;
  speed?: number;
  geometry?: any;
  properties: Record<string, any>;
  provenance: {
    sourceId: string;
    sourceName: string;
    retrievedAt: string;
    sourceTimestamp?: string;
    sourceReference?: string;
    sourceUrl?: string;
    dataset?: string;
    version?: string;
  };
  rawReference?: string;
}

export interface SourceAdapter {
  id: string;
  name: string;
  category: string;
  status: SourceStatus;
  configured: boolean;
  requiresServer: boolean;
  lastFetch?: string;
  lastSuccess?: string;
  lastError?: string;
  refreshInterval?: number;
  provenance: string;
  entityCount: number;
  
  fetchData(): Promise<GeoEntity[]>;
  normalize(raw: any): GeoEntity[];
  isEnabled(): boolean;
  enable(): void;
  disable(): void;
}

export interface SourceRegistry {
  sources: Map<string, SourceAdapter>;
  get(id: string): SourceAdapter | undefined;
  getAll(): SourceAdapter[];
  getByCategory(category: string): SourceAdapter[];
  register(adapter: SourceAdapter): void;
  getStatus(id: string): SourceStatus;
}

export class SourceRegistryImpl implements SourceRegistry {
  sources: Map<string, SourceAdapter> = new Map();

  get(id: string): SourceAdapter | undefined {
    return this.sources.get(id);
  }

  getAll(): SourceAdapter[] {
    return Array.from(this.sources.values());
  }

  getByCategory(category: string): SourceAdapter[] {
    return this.getAll().filter(s => s.category === category);
  }

  register(adapter: SourceAdapter): void {
    this.sources.set(adapter.id, adapter);
  }

  getStatus(id: string): SourceStatus {
    const source = this.sources.get(id);
    return source ? source.status : 'UNAVAILABLE';
  }
}

// Global registry instance
export const sourceRegistry = new SourceRegistryImpl();
