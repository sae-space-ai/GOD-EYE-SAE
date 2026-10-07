import { useEffect, useRef, useCallback, useState } from 'react';
import * as Cesium from 'cesium';

// Module-level viewer ref for export
let _viewerRef: Cesium.Viewer | null = null;

import type { GeoEntity } from '../services/sources/types';

interface GlobeProps {
  className?: string;
  onCoordinateChange?: (lat: number, lng: number) => void;
  onViewerReady?: (viewer: Cesium.Viewer) => void;
  entities?: GeoEntity[];
  onEntitySelect?: (entity: GeoEntity) => void;
}

export default function Globe({ className = '', onCoordinateChange, onViewerReady, entities = [], onEntitySelect }: GlobeProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<Cesium.Viewer | null>(null);
  const [isReady, setIsReady] = useState(false);

  const initCesium = useCallback(() => {
    if (!containerRef.current || viewerRef.current) return;

    // Cesium Ion default access token
    // The upstream God's Eye View uses a keyless start pattern with Esri imagery
    // and optional Cesium ion token for 3D Tiles. We use a minimal community token
    // for basic terrain access.
    Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI3OGRhMWE0Zi0xMmQ3LTRiMGYtOWI1Yi1kYTQ2MzRkNTYzNzQiLCJpZCI6MjY3NjQsImlhdCI6MTY3NzYyODg0NX0.sample';

    try {
      const viewer = new Cesium.Viewer(containerRef.current, {
        // Basemap: Esri World Imagery (keyless, same as upstream God's Eye View)
        baseLayer: Cesium.ImageryLayer.fromProviderAsync(
          Cesium.ArcGisMapServerImageryProvider.fromUrl(
            'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer'
          )
        ),
        // UI controls - disabled for clean command center look
        animation: false,
        baseLayerPicker: false,
        geocoder: false,
        homeButton: false,
        infoBox: false,
        navigationHelpButton: false,
        projectionPicker: false,
        sceneModePicker: false,
        selectionIndicator: false,
        timeline: false,
        fullscreenButton: false,
        vrButton: false,
        // Scene settings
        scene3DOnly: true,
        shouldAnimate: true,
      });

      // Scene configuration
      viewer.scene.globe.enableLighting = true;
      viewer.scene.globe.depthTestAgainstTerrain = false;
      if (viewer.scene.fog) {
        viewer.scene.fog.enabled = true;
        viewer.scene.fog.density = 0.0002;
      }
      if (viewer.scene.skyAtmosphere) {
        viewer.scene.skyAtmosphere.show = true;
      }

      // Initial camera position - view of Earth
      viewer.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(0, 20, 20000000),
        duration: 0,
      });

      // Mouse move handler for coordinates
      const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
      
      handler.setInputAction((movement: Cesium.ScreenSpaceEventHandler.MotionEvent) => {
        const cartesian = viewer.camera.pickEllipsoid(
          movement.endPosition,
          viewer.scene.globe.ellipsoid
        );
        if (cartesian && onCoordinateChange) {
          const cartographic = Cesium.Cartographic.fromCartesian(cartesian);
          const lat = Cesium.Math.toDegrees(cartographic.latitude);
          const lng = Cesium.Math.toDegrees(cartographic.longitude);
          onCoordinateChange(
            Math.round(lat * 100) / 100,
            Math.round(lng * 100) / 100
          );
        }
      }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);

      // Click handler for entity selection
      handler.setInputAction((click: Cesium.ScreenSpaceEventHandler.PositionedEvent) => {
        const pickedObject = viewer.scene.pick(click.position);
        if (Cesium.defined(pickedObject) && pickedObject.id) {
          const cesiumEntity = pickedObject.id;
          const geoEntity = (cesiumEntity as any)._geoEntity;
          if (geoEntity && onEntitySelect) {
            onEntitySelect(geoEntity);
          }
          console.log('Entity selected:', geoEntity || cesiumEntity.id);
        }
      }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

      viewerRef.current = viewer;
      _viewerRef = viewer;
      setIsReady(true);
      
      if (onViewerReady) {
        onViewerReady(viewer);
      }

      // Load USGS earthquake data (keyless, real data - same as upstream)
      loadEarthquakeData(viewer);

    } catch (error) {
      console.error('Error initializing Cesium:', error);
    }
  }, [onCoordinateChange, onViewerReady]);

  useEffect(() => {
    initCesium();

    return () => {
      if (viewerRef.current) {
        viewerRef.current.destroy();
        viewerRef.current = null;
        _viewerRef = null;
      }
    };
  }, [initCesium]);

  // Update entities on the globe
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) return;

    // Remove existing dynamic entities
    const entitiesToRemove: string[] = [];
    viewer.entities.values.forEach(entity => {
      if (entity.id.startsWith('dynamic_')) {
        entitiesToRemove.push(entity.id);
      }
    });
    entitiesToRemove.forEach(id => viewer.entities.removeById(id));

    // Add new entities
    entities.forEach((geoEntity, index) => {
      let color: Cesium.Color;
      let pixelSize = 8;

      switch (geoEntity.type) {
        case 'earthquake':
          const mag = geoEntity.properties.magnitude || 2.5;
          if (mag >= 6) color = Cesium.Color.RED;
          else if (mag >= 5) color = Cesium.Color.ORANGE;
          else if (mag >= 4) color = Cesium.Color.YELLOW;
          else color = Cesium.Color.CYAN;
          pixelSize = Math.min(Math.max(mag * 2, 4), 16);
          break;
        case 'satellite':
          color = Cesium.Color.fromCssColorString('#00ff88');
          pixelSize = 6;
          break;
        case 'aircraft':
          color = Cesium.Color.fromCssColorString('#ff6b35');
          pixelSize = 5;
          break;
        default:
          color = Cesium.Color.WHITE;
      }

      const entity = viewer.entities.add({
        id: `dynamic_${geoEntity.id}_${index}`,
        position: Cesium.Cartesian3.fromDegrees(
          geoEntity.position.longitude,
          geoEntity.position.latitude,
          geoEntity.position.altitude || 0
        ),
        point: {
          pixelSize,
          color: color.withAlpha(0.8),
          outlineColor: Cesium.Color.WHITE.withAlpha(0.3),
          outlineWidth: 1,
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
        },
        properties: {
          geoEntity: geoEntity,
        },
      });

      // Store reference for selection
      (entity as any)._geoEntity = geoEntity;
    });
  }, [entities]);

  return (
    <div
      ref={containerRef}
      className={`w-full h-full ${className}`}
      role="application"
      aria-label="Globo Cesium 3D interactivo — God's Eye View"
      style={{ minHeight: '100%' }}
    />
  );
}

/**
 * Load real USGS earthquake data (keyless, public API)
 * Based on upstream God's Eye View earthquake layer pattern.
 * Source: https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson
 * License: Public Domain (USGS)
 */
async function loadEarthquakeData(viewer: Cesium.Viewer) {
  try {
    const response = await fetch(
      'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson'
    );
    
    if (!response.ok) return;
    
    const data = await response.json();
    
    if (!data.features) return;

    const earthquakeEntities: Cesium.Entity[] = [];

    data.features.forEach((feature: any) => {
      const [lng, lat] = feature.geometry.coordinates;
      const magnitude = feature.properties.mag;
      const place = feature.properties.place;
      const time = new Date(feature.properties.time);

      // Color based on magnitude
      let color: Cesium.Color;
      if (magnitude >= 6) {
        color = Cesium.Color.RED.withAlpha(0.8);
      } else if (magnitude >= 5) {
        color = Cesium.Color.ORANGE.withAlpha(0.7);
      } else if (magnitude >= 4) {
        color = Cesium.Color.YELLOW.withAlpha(0.6);
      } else {
        color = Cesium.Color.CYAN.withAlpha(0.5);
      }

      const entity = viewer.entities.add({
        position: Cesium.Cartesian3.fromDegrees(lng, lat),
        point: {
          pixelSize: Math.min(Math.max(magnitude * 2, 4), 12),
          color: color,
          outlineColor: Cesium.Color.WHITE.withAlpha(0.3),
          outlineWidth: 1,
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
        },
        properties: {
          type: 'earthquake',
          magnitude: magnitude,
          place: place,
          time: time.toISOString(),
          source: 'USGS',
          depth: feature.geometry.coordinates[2],
        },
      });

      earthquakeEntities.push(entity);
    });

    // Store reference for layer management
    (viewer as any)._earthquakeEntities = earthquakeEntities;
    (viewer as any)._earthquakeData = data;

  } catch (error) {
    console.warn('Could not load USGS earthquake data:', error);
  }
}

/**
 * Export viewer for external access (layer management, etc.)
 */
export function getViewer(): Cesium.Viewer | null {
  return _viewerRef;
}
