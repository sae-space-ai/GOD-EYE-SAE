/**
 * USGS Earthquake Source Adapter
 * 
 * Fetches real earthquake data from USGS Earthquake Hazards Program.
 * Keyless, public API with CORS support.
 * 
 * Source: https://earthquake.usgs.gov/fdsnws/event/1/
 * License: Public Domain (USGS)
 * 
 * Based on upstream God's Eye View earthquake layer pattern.
 */

import type { SourceAdapter, GeoEntity, SourceStatus } from './types';

const USGS_API_URL = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson';

export class USGSEarthquakeAdapter implements SourceAdapter {
  id = 'usgs-earthquakes';
  name = 'USGS Earthquakes';
  category = 'earthquakes';
  status: SourceStatus = 'INTEGRATED_VERIFIED';
  configured = true;
  requiresServer = false;
  lastFetch?: string;
  lastSuccess?: string;
  lastError?: string;
  refreshInterval = 60000; // 1 minute
  provenance = 'USGS Earthquake Hazards Program';
  entityCount = 0;
  private enabled = true;
  private entities: GeoEntity[] = [];

  async fetchData(): Promise<GeoEntity[]> {
    if (!this.enabled) return [];
    
    this.lastFetch = new Date().toISOString();
    
    try {
      const response = await fetch(USGS_API_URL);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      this.entities = this.normalize(data);
      this.entityCount = this.entities.length;
      this.lastSuccess = new Date().toISOString();
      this.status = 'INTEGRATED_VERIFIED';
      
      return this.entities;
    } catch (error) {
      this.lastError = error instanceof Error ? error.message : String(error);
      this.status = 'ERROR';
      console.error('USGS fetch error:', error);
      return [];
    }
  }

  normalize(data: any): GeoEntity[] {
    if (!data.features) return [];
    
    return data.features.map((feature: any) => {
      const [lng, lat, depth] = feature.geometry.coordinates;
      const props = feature.properties;
      
      return {
        id: props.id || `eq_${Date.now()}_${Math.random()}`,
        sourceId: this.id,
        type: 'earthquake',
        subtype: 'seismic',
        name: props.place || 'Unknown location',
        timestamp: new Date(props.time).toISOString(),
        position: {
          longitude: lng,
          latitude: lat,
          altitude: -depth * 1000, // Convert km to meters (negative = below surface)
        },
        properties: {
          magnitude: props.mag,
          place: props.place,
          time: props.time,
          updated: props.updated,
          tz: props.tz,
          url: props.url,
          detail: props.detail,
          felt: props.felt,
          sig: props.sig,
          net: props.net,
          code: props.code,
          ids: props.ids,
          sources: props.sources,
          types: props.types,
          nst: props.nst,
          dmin: props.dmin,
          rms: props.rms,
          gap: props.gap,
          magType: props.magType,
          type: props.type,
          depth: depth,
        },
        provenance: {
          sourceId: this.id,
          sourceName: this.name,
          retrievedAt: new Date().toISOString(),
          sourceTimestamp: new Date(props.time).toISOString(),
          sourceReference: props.code,
          sourceUrl: props.url,
          dataset: 'USGS Earthquake Hazards Program',
          version: '1.0',
        },
      };
    });
  }

  isEnabled(): boolean {
    return this.enabled;
  }

  enable(): void {
    this.enabled = true;
    this.status = 'INTEGRATED_VERIFIED';
  }

  disable(): void {
    this.enabled = false;
    this.status = 'DISABLED';
    this.entities = [];
    this.entityCount = 0;
  }

  getEntities(): GeoEntity[] {
    return this.entities;
  }
}
