/**
 * CelesTrak Satellite Source Adapter
 * 
 * Fetches TLE data from CelesTrak and propagates orbits using satellite.js.
 * Keyless, public API.
 * 
 * Source: https://celestrak.org/NORAD/elements/gp.php
 * Library: satellite.js (SGP4 propagation)
 * License: Public (CelesTrak) + MIT (satellite.js)
 * 
 * Based on upstream God's Eye View satellite layer pattern.
 */

import * as satellite from 'satellite.js';
import type { SourceAdapter, GeoEntity, SourceStatus } from './types';

const CELESTRAK_URL = 'https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle';

export class CelesTrakSatelliteAdapter implements SourceAdapter {
  id = 'celestrak-satellites';
  name = 'CelesTrak Satellites';
  category = 'satellites';
  status: SourceStatus = 'INTEGRATED_UNVERIFIED';
  configured = true;
  requiresServer = false;
  lastFetch?: string;
  lastSuccess?: string;
  lastError?: string;
  refreshInterval = 300000; // 5 minutes
  provenance = 'CelesTrak';
  entityCount = 0;
  private enabled = true;
  private entities: GeoEntity[] = [];
  private satellites: Array<{ tle: any; name: string; noradId: string }> = [];
  private maxSatellites = 100; // Limit for performance

  async fetchData(): Promise<GeoEntity[]> {
    if (!this.enabled) return [];
    
    this.lastFetch = new Date().toISOString();
    
    try {
      const response = await fetch(CELESTRAK_URL);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const tleText = await response.text();
      this.satellites = this.parseTLE(tleText);
      
      // Limit to maxSatellites for performance
      this.satellites = this.satellites.slice(0, this.maxSatellites);
      
      this.entities = this.propagateAll();
      this.entityCount = this.entities.length;
      this.lastSuccess = new Date().toISOString();
      this.status = 'INTEGRATED_VERIFIED';
      
      return this.entities;
    } catch (error) {
      this.lastError = error instanceof Error ? error.message : String(error);
      this.status = 'ERROR';
      console.error('CelesTrak fetch error:', error);
      return [];
    }
  }

  /**
   * Parse TLE text into satellite records
   */
  private parseTLE(text: string): Array<{ tle: any; name: string; noradId: string }> {
    const lines = text.trim().split('\n');
    const satellites: Array<{ tle: any; name: string; noradId: string }> = [];
    
    for (let i = 0; i < lines.length - 2; i += 3) {
      const name = lines[i].trim();
      const line1 = lines[i + 1].trim();
      const line2 = lines[i + 2].trim();
      
      try {
        const satrec = satellite.twoline2satrec(line1, line2);
        const noradId = line1.substring(2, 7).trim();
        satellites.push({ tle: satrec, name, noradId });
      } catch (error) {
        console.warn(`Failed to parse TLE for ${name}:`, error);
      }
    }
    
    return satellites;
  }

  /**
   * Propagate all satellites to current time
   */
  private propagateAll(): GeoEntity[] {
    const now = new Date();
    const results: GeoEntity[] = [];
    
    for (let i = 0; i < this.satellites.length; i++) {
      const sat = this.satellites[i];
      try {
        const positionAndVelocity = satellite.propagate(sat.tle, now);
        
        if (!positionAndVelocity || !positionAndVelocity.position || typeof positionAndVelocity.position === 'boolean') {
          continue;
        }
        
        const positionEci = positionAndVelocity.position as satellite.EciVec3<number>;
        const gmst = satellite.gstime(now);
        const positionGd = satellite.eciToGeodetic(positionEci, gmst);
        
        const longitude = satellite.degreesLong(positionGd.longitude);
        const latitude = satellite.degreesLat(positionGd.latitude);
        const altitude = positionGd.height * 1000; // km to meters
        
        results.push({
          id: `sat_${sat.noradId}_${i}`,
          sourceId: this.id,
          type: 'satellite',
          subtype: 'active',
          name: sat.name,
          timestamp: now.toISOString(),
          position: {
            longitude,
            latitude,
            altitude,
          },
          properties: {
            noradId: sat.noradId,
            name: sat.name,
            altitudeKm: positionGd.height,
          },
          provenance: {
            sourceId: this.id,
            sourceName: this.name,
            retrievedAt: now.toISOString(),
            sourceTimestamp: now.toISOString(),
            sourceReference: sat.noradId,
            sourceUrl: `https://celestrak.org/NORAD/elements/gp.php?CATNR=${sat.noradId}`,
            dataset: 'CelesTrak Active Satellites',
            version: '1.0',
          },
        });
      } catch (error) {
        console.warn(`Propagation failed for ${sat.name}:`, error);
      }
    }
    
    return results;
  }

  normalize(raw: any): GeoEntity[] {
    // Already normalized in fetchData
    return this.entities;
  }

  isEnabled(): boolean {
    return this.enabled;
  }

  enable(): void {
    this.enabled = true;
    this.status = 'INTEGRATED_UNVERIFIED';
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
