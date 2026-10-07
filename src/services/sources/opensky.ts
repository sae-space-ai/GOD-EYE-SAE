/**
 * OpenSky Network Source Adapter
 * 
 * Fetches live aircraft data from OpenSky Network.
 * Anonymous access available with rate limits.
 * 
 * Source: https://opensky-network.org/apidoc/rest.php
 * License: OpenSky Terms of Use
 * 
 * Based on upstream God's Eye View aircraft layer pattern.
 */

import type { SourceAdapter, GeoEntity, SourceStatus } from './types';

const OPENSKY_API_URL = 'https://opensky-network.org/api/states/all';

export class OpenSkyFlightAdapter implements SourceAdapter {
  id = 'opensky-flights';
  name = 'OpenSky Flights';
  category = 'aircraft';
  status: SourceStatus = 'INTEGRATED_UNVERIFIED';
  configured = true;
  requiresServer = false; // Can work keyless with rate limits
  lastFetch?: string;
  lastSuccess?: string;
  lastError?: string;
  refreshInterval = 15000; // 15 seconds (respect rate limits)
  provenance = 'OpenSky Network';
  entityCount = 0;
  private enabled = true;
  private entities: GeoEntity[] = [];
  private maxAircraft = 500; // Limit for performance

  async fetchData(): Promise<GeoEntity[]> {
    if (!this.enabled) return [];
    
    this.lastFetch = new Date().toISOString();
    
    try {
      const response = await fetch(OPENSKY_API_URL, {
        headers: {
          'Accept': 'application/json',
        },
      });
      
      if (!response.ok) {
        if (response.status === 429) {
          this.status = 'ERROR';
          this.lastError = 'Rate limit exceeded (HTTP 429)';
          return this.entities; // Keep last valid data
        }
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
      console.error('OpenSky fetch error:', error);
      return this.entities; // Keep last valid data on error
    }
  }

  normalize(data: any): GeoEntity[] {
    if (!data.states || !Array.isArray(data.states)) return [];
    
    const now = new Date().toISOString();
    
    // Limit to maxAircraft for performance
    const states = data.states.slice(0, this.maxAircraft);
    
    return states.map((state: any[], index: number) => {
      // OpenSky state vector format:
      // [0] icao24, [1] callsign, [2] origin_country, [3] time_position,
      // [4] last_contact, [5] longitude, [6] latitude, [7] baro_altitude,
      // [8] on_ground, [9] velocity, [10] true_track, [11] vertical_rate,
      // [12] sensors, [13] geo_altitude, [14] squawk, [15] spi, [16] position_source
      
      const [
        icao24, callsign, originCountry, timePosition,
        lastContact, longitude, latitude, baroAltitude,
        onGround, velocity, trueTrack, verticalRate,
        , geoAltitude, squawk, spi, positionSource
      ] = state;
      
      // Skip aircraft without position
      if (longitude === null || latitude === null) {
        return null;
      }
      
      return {
        id: `flight_${icao24}_${index}`,
        sourceId: this.id,
        type: 'aircraft',
        subtype: onGround ? 'grounded' : 'airborne',
        name: callsign?.trim() || icao24,
        timestamp: new Date((timePosition || Date.now() / 1000) * 1000).toISOString(),
        position: {
          longitude,
          latitude,
          altitude: (geoAltitude || baroAltitude || 0),
        },
        heading: trueTrack || undefined,
        speed: velocity || undefined,
        properties: {
          icao24,
          callsign: callsign?.trim(),
          originCountry,
          timePosition,
          lastContact,
          baroAltitude,
          onGround,
          velocity,
          trueTrack,
          verticalRate,
          geoAltitude,
          squawk,
          spi,
          positionSource,
        },
        provenance: {
          sourceId: this.id,
          sourceName: this.name,
          retrievedAt: now,
          sourceTimestamp: new Date((timePosition || Date.now() / 1000) * 1000).toISOString(),
          sourceReference: icao24,
          sourceUrl: `https://opensky-network.org/aircraft-profile?icao24=${icao24}`,
          dataset: 'OpenSky Network States',
          version: '1.0',
        },
      };
    }).filter((e: GeoEntity | null): e is GeoEntity => e !== null);
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
