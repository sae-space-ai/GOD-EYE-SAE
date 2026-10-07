export type ResourceStatus = 
  | 'active' 
  | 'inactive' 
  | 'notConfigured' 
  | 'notAvailable' 
  | 'error' 
  | 'loading' 
  | 'experimental'
  | 'operational'
  | 'comingSoon'
  | 'requiresConfig'
  | 'partial';

export type ResourceCategory =
  | 'dataLayers'
  | 'sources'
  | 'scenes'
  | 'missions'
  | 'territory'
  | 'earthObservation'
  | 'satellites'
  | 'fires'
  | 'weather'
  | 'earthquakes'
  | 'aircraft'
  | 'vessels'
  | 'cameras'
  | 'infrastructure'
  | 'documents'
  | 'evidence'
  | 'alerts';

export interface Resource {
  id: string;
  type: string;
  category: ResourceCategory;
  name: string;
  description: string;
  source?: string;
  status: ResourceStatus;
  enabled: boolean;
  available: boolean;
  requiresAuth: boolean;
  lastUpdated?: string;
  metadata?: Record<string, unknown>;
}

export interface DataSource {
  id: string;
  name: string;
  organization: string;
  type: string;
  url?: string;
  category: ResourceCategory;
  license?: string;
  updateFrequency?: string;
  geographicScope?: string;
  requiresAuth: boolean;
  envVariable?: string;
  status: ResourceStatus;
}

export interface SelectedEntity {
  id: string;
  name: string;
  type: string;
  coordinates?: { lat: number; lng: number; alt?: number };
  source?: string;
  timestamp?: string;
  metadata?: Record<string, unknown>;
}

export type OperationalMode = 'operational' | 'eo' | 'osint' | 'firecycle' | 'evidence' | 'aiAnalysis';

export type MicrophoneState = 'deactivated' | 'ready' | 'listening' | 'processing' | 'executing' | 'error';

export interface MissionOption {
  id: string;
  titleKey: string;
  descriptionKey: string;
  icon: string;
  available: boolean;
}

export interface Evidence {
  id: string;
  missionId?: string;
  sourceId?: string;
  entityId?: string;
  timestamp: string;
  retrievedAt: string;
  coordinates?: { lat: number; lng: number };
  bbox?: [number, number, number, number];
  sourceUrl?: string;
  sourceType?: string;
  mimeType?: string;
  hash?: string;
  metadata?: Record<string, unknown>;
  confidence?: number;
  status: 'captured' | 'verified' | 'rejected' | 'pending' | 'superseded';
  createdAt: string;
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  resource: string;
  resourceId?: string;
  missionId?: string;
  input?: unknown;
  output?: unknown;
  source?: string;
  status: string;
  metadata?: Record<string, unknown>;
}
