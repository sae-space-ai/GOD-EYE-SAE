/**
 * useSources Hook
 * 
 * Manages source adapters and provides reactive state for the UI.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { USGSEarthquakeAdapter } from '../services/sources/usgs';
import { CelesTrakSatelliteAdapter } from '../services/sources/celestrak';
import { OpenSkyFlightAdapter } from '../services/sources/opensky';
import { sourceRegistry } from '../services/sources/types';
import type { SourceAdapter, GeoEntity } from '../services/sources/types';
import { recordAuditEvent } from '../services/audit/engine';

export interface SourceState {
  adapter: SourceAdapter;
  entities: GeoEntity[];
  lastUpdate: string | null;
  error: string | null;
}

export function useSources() {
  const [sources, setSources] = useState<Map<string, SourceState>>(new Map());
  const [isInitialized, setIsInitialized] = useState(false);
  const intervalsRef = useRef<Map<string, NodeJS.Timeout>>(new Map());

  // Initialize source adapters
  useEffect(() => {
    if (isInitialized) return;

    const usgs = new USGSEarthquakeAdapter();
    const celestrak = new CelesTrakSatelliteAdapter();
    const opensky = new OpenSkyFlightAdapter();

    sourceRegistry.register(usgs);
    sourceRegistry.register(celestrak);
    sourceRegistry.register(opensky);

    setSources(new Map([
      ['usgs-earthquakes', { adapter: usgs, entities: [], lastUpdate: null, error: null }],
      ['celestrak-satellites', { adapter: celestrak, entities: [], lastUpdate: null, error: null }],
      ['opensky-flights', { adapter: opensky, entities: [], lastUpdate: null, error: null }],
    ]));

    setIsInitialized(true);
  }, [isInitialized]);

  // Fetch data from a source
  const fetchSource = useCallback(async (sourceId: string) => {
    const adapter = sourceRegistry.get(sourceId);
    if (!adapter) return;

    try {
      await recordAuditEvent('SOURCE_FETCH_STARTED', 'source', {
        resourceId: sourceId,
        status: 'pending',
      });

      const entities = await adapter.fetchData();

      setSources(prev => {
        const next = new Map(prev);
        const state = next.get(sourceId);
        if (state) {
          next.set(sourceId, {
            ...state,
            entities,
            lastUpdate: new Date().toISOString(),
            error: null,
          });
        }
        return next;
      });

      await recordAuditEvent('SOURCE_FETCH_SUCCEEDED', 'source', {
        resourceId: sourceId,
        metadata: { entityCount: entities.length },
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      
      setSources(prev => {
        const next = new Map(prev);
        const state = next.get(sourceId);
        if (state) {
          next.set(sourceId, {
            ...state,
            error: errorMessage,
          });
        }
        return next;
      });

      await recordAuditEvent('SOURCE_FETCH_FAILED', 'source', {
        resourceId: sourceId,
        status: 'failure',
        metadata: { error: errorMessage },
      });
    }
  }, []);

  // Enable a source
  const enableSource = useCallback(async (sourceId: string) => {
    const adapter = sourceRegistry.get(sourceId);
    if (!adapter) return;

    adapter.enable();
    
    setSources(prev => {
      const next = new Map(prev);
      const state = next.get(sourceId);
      if (state) {
        next.set(sourceId, { ...state, adapter });
      }
      return next;
    });

    await recordAuditEvent('SOURCE_ENABLED', 'source', {
      resourceId: sourceId,
    });

    // Start fetching
    await fetchSource(sourceId);
  }, [fetchSource]);

  // Disable a source
  const disableSource = useCallback(async (sourceId: string) => {
    const adapter = sourceRegistry.get(sourceId);
    if (!adapter) return;

    adapter.disable();
    
    setSources(prev => {
      const next = new Map(prev);
      const state = next.get(sourceId);
      if (state) {
        next.set(sourceId, { ...state, adapter, entities: [] });
      }
      return next;
    });

    // Stop interval
    const interval = intervalsRef.current.get(sourceId);
    if (interval) {
      clearInterval(interval);
      intervalsRef.current.delete(sourceId);
    }

    await recordAuditEvent('SOURCE_DISABLED', 'source', {
      resourceId: sourceId,
    });
  }, []);

  // Start auto-refresh for a source
  const startAutoRefresh = useCallback((sourceId: string, intervalMs?: number) => {
    const adapter = sourceRegistry.get(sourceId);
    if (!adapter) return;

    const interval = intervalMs || adapter.refreshInterval || 60000;

    // Clear existing interval
    const existing = intervalsRef.current.get(sourceId);
    if (existing) clearInterval(existing);

    const newInterval = setInterval(() => {
      fetchSource(sourceId);
    }, interval);

    intervalsRef.current.set(sourceId, newInterval);
  }, [fetchSource]);

  // Stop auto-refresh for a source
  const stopAutoRefresh = useCallback((sourceId: string) => {
    const interval = intervalsRef.current.get(sourceId);
    if (interval) {
      clearInterval(interval);
      intervalsRef.current.delete(sourceId);
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      intervalsRef.current.forEach(interval => clearInterval(interval));
      intervalsRef.current.clear();
    };
  }, []);

  return {
    sources,
    isInitialized,
    fetchSource,
    enableSource,
    disableSource,
    startAutoRefresh,
    stopAutoRefresh,
    getAllEntities: (): GeoEntity[] => {
      const all: GeoEntity[] = [];
      sources.forEach(state => {
        all.push(...state.entities);
      });
      return all;
    },
  };
}
