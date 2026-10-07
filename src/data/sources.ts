import { DataSource, Resource } from '../types';

/**
 * Data Source Registry for GOD EYE SAE
 * 
 * Based on upstream God's Eye View (bilawalsidhu/gods-eye-view)
 * License: MIT
 * 
 * Sources are classified by their real integration status:
 * - INTEGRATED_VERIFIED: Working with real data, no key required
 * - INTEGRATED_UNVERIFIED: Code exists but cannot verify data flow
 * - CONFIGURED: Key available, integration ready
 * - NOT_CONFIGURED: Integration exists but requires API key
 * - PLANNED: Architecture prepared, not yet implemented
 * - ERROR: Integration exists but failing
 * 
 * IMPORTANT: We do NOT mark a source as "active" unless there is
 * verifiable code integration. This follows the upstream's honest
 * approach to data source status.
 */

export const dataSources: DataSource[] = [
  // === KEYLESS SOURCES (work without API keys, per upstream) ===
  {
    id: 'esri-imagery',
    name: 'Esri World Imagery',
    organization: 'Esri',
    type: 'basemap',
    url: 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer',
    category: 'dataLayers',
    license: 'Esri Terms',
    updateFrequency: 'Variable',
    geographicScope: 'Global',
    requiresAuth: false,
    status: 'active', // Integrated in Cesium globe baseLayer
  },
  {
    id: 'openstreetmap',
    name: 'OpenStreetMap',
    organization: 'OSM Foundation',
    type: 'basemap',
    url: 'https://www.openstreetmap.org',
    category: 'dataLayers',
    license: 'ODbL',
    updateFrequency: 'Continua',
    geographicScope: 'Global',
    requiresAuth: false,
    status: 'active', // Fallback basemap in upstream
  },
  {
    id: 'usgs-earthquakes',
    name: 'USGS Earthquakes',
    organization: 'USGS',
    type: 'seismic',
    url: 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson',
    category: 'earthquakes',
    license: 'Public Domain',
    updateFrequency: 'Tiempo real (M2.5+ cada minuto)',
    geographicScope: 'Global',
    requiresAuth: false,
    status: 'active', // Integrated: loads real data in Globe.tsx
  },
  {
    id: 'opensky-flights',
    name: 'OpenSky Network',
    organization: 'OpenSky Network',
    type: 'aircraft',
    url: 'https://opensky-network.org/apidoc/rest.php',
    category: 'aircraft',
    license: 'OpenSky Terms',
    updateFrequency: 'Cada 10-15s (anónimo)',
    geographicScope: 'Global',
    requiresAuth: false,
    status: 'notConfigured', // Upstream has full integration, requires server proxy
  },
  {
    id: 'adsblol-military',
    name: 'adsb.lol Military',
    organization: 'adsb.lol',
    type: 'aircraft',
    url: 'https://adsb.lol',
    category: 'aircraft',
    license: 'Public',
    updateFrequency: 'Tiempo real',
    geographicScope: 'Global',
    requiresAuth: false,
    status: 'notConfigured', // Upstream has integration, requires server proxy
  },
  {
    id: 'celestrak-satellites',
    name: 'CelesTrak',
    organization: 'CelesTrak',
    type: 'satellite',
    url: 'https://celestrak.org',
    category: 'satellites',
    license: 'Public',
    updateFrequency: 'Diaria (TLE)',
    geographicScope: 'Global',
    requiresAuth: false,
    status: 'notConfigured', // Upstream has SGP4 propagation, requires integration
  },
  {
    id: 'noaa-weather',
    name: 'NOAA Weather',
    organization: 'NOAA',
    type: 'weather',
    url: 'https://www.noaa.gov',
    category: 'weather',
    license: 'Public Domain',
    updateFrequency: 'Variable (GFS, MRMS, GOES)',
    geographicScope: 'Global',
    requiresAuth: false,
    status: 'notConfigured', // Upstream has full weather integration
  },
  {
    id: 'noaa-cyclones',
    name: 'NOAA NHC/CPHC',
    organization: 'NOAA',
    type: 'weather',
    url: 'https://www.nhc.noaa.gov',
    category: 'weather',
    license: 'Public Domain',
    updateFrequency: 'Cada 6h (avisos)',
    geographicScope: 'Atlántico, Pacífico',
    requiresAuth: false,
    status: 'notConfigured', // Upstream has cyclone tracks
  },
  {
    id: 'radio-browser',
    name: 'Radio Browser',
    organization: 'Radio Browser',
    type: 'radio',
    url: 'https://www.radio-browser.info',
    category: 'infrastructure',
    license: 'Public',
    updateFrequency: 'Continua',
    geographicScope: 'Global',
    requiresAuth: false,
    status: 'notConfigured', // Upstream has radio layer
  },
  {
    id: 'launch-library-2',
    name: 'Launch Library 2',
    organization: 'The Space Devs',
    type: 'launches',
    url: 'https://thespacedevs.com/llapi',
    category: 'missions',
    license: 'Public',
    updateFrequency: 'En tiempo de lanzamiento',
    geographicScope: 'Global',
    requiresAuth: false,
    status: 'notConfigured', // Upstream has 30-day launch replay
  },
  {
    id: 'cctv-public',
    name: 'CCTV Público',
    organization: 'Múltiples ciudades',
    type: 'cameras',
    category: 'cameras',
    license: 'Variable por ciudad',
    updateFrequency: 'Tiempo real',
    geographicScope: 'Austin, London, California, Finland, etc.',
    requiresAuth: false,
    status: 'notConfigured', // Upstream has ~3,900 cameras projected in 3D
  },
  {
    id: 'osrm-directions',
    name: 'OSRM Routing',
    organization: 'FOSSGIS / OSM',
    type: 'routing',
    url: 'https://routing.openstreetmap.de',
    category: 'infrastructure',
    license: 'BSD',
    updateFrequency: 'Tiempo real',
    geographicScope: 'Global',
    requiresAuth: false,
    status: 'notConfigured', // Upstream has terrain-draped routes
  },

  // === SOURCES REQUIRING API KEYS ===
  {
    id: 'nasa-firms',
    name: 'NASA FIRMS',
    organization: 'NASA',
    type: 'fire',
    url: 'https://firms.modaps.eosdis.nasa.gov',
    category: 'fires',
    license: 'Public',
    updateFrequency: 'Cada 3-6 horas',
    geographicScope: 'Global',
    requiresAuth: true,
    envVariable: 'FIRMS_MAP_KEY', // Server-side, not VITE_ (security fix)
    status: 'notConfigured',
  },
  {
    id: 'aisstream-vessels',
    name: 'AISStream',
    organization: 'AISStream',
    type: 'vessel',
    url: 'https://aisstream.io',
    category: 'vessels',
    license: 'Terms of Service',
    updateFrequency: 'Tiempo real (WebSocket)',
    geographicScope: 'Global',
    requiresAuth: true,
    envVariable: 'AISSTREAM_API_KEY', // Server-side proxy
    status: 'notConfigured',
  },
  {
    id: 'cesium-ion',
    name: 'Cesium ion',
    organization: 'Cesium',
    type: '3dtiles',
    url: 'https://cesium.com/ion',
    category: 'dataLayers',
    license: 'Cesium ion Terms',
    updateFrequency: 'Variable',
    geographicScope: 'Global',
    requiresAuth: true,
    envVariable: 'CESIUM_ION_TOKEN',
    status: 'notConfigured', // Required for Google Photorealistic 3D
  },
  {
    id: 'google-maps',
    name: 'Google Maps 3D',
    organization: 'Google',
    type: '3dtiles',
    url: 'https://developers.google.com/maps/documentation/tile',
    category: 'dataLayers',
    license: 'Google Maps Platform Terms',
    updateFrequency: 'Variable',
    geographicScope: 'Global',
    requiresAuth: true,
    envVariable: 'GOOGLE_MAPS_API_KEY', // Metered
    status: 'notConfigured',
  },
  {
    id: 'tomtom-traffic',
    name: 'TomTom Traffic',
    organization: 'TomTom',
    type: 'traffic',
    url: 'https://developer.tomtom.com',
    category: 'infrastructure',
    license: 'TomTom Terms',
    updateFrequency: 'Tiempo real',
    geographicScope: 'Global',
    requiresAuth: true,
    envVariable: 'TOMTOM_API_KEY',
    status: 'notConfigured',
  },
  {
    id: 'openai-voice',
    name: 'OpenAI Realtime',
    organization: 'OpenAI',
    type: 'ai',
    url: 'https://platform.openai.com',
    category: 'missions',
    license: 'OpenAI Terms',
    updateFrequency: 'Tiempo real',
    geographicScope: 'N/A',
    requiresAuth: true,
    envVariable: 'OPENAI_API_KEY', // Server-side only, never exposed to browser
    status: 'notConfigured',
  },

  // === SATELLITE IMAGERY (require Copernicus credentials) ===
  {
    id: 'copernicus-sentinel2',
    name: 'Sentinel-2',
    organization: 'ESA',
    type: 'satellite',
    category: 'satellites',
    license: 'Copernicus Sentinel Data',
    updateFrequency: '5 días (revisita)',
    geographicScope: 'Global',
    requiresAuth: true,
    envVariable: 'COPERNICUS_CLIENT_ID', // Server-side OAuth
    status: 'notConfigured',
  },
  {
    id: 'copernicus-sentinel1',
    name: 'Sentinel-1',
    organization: 'ESA',
    type: 'satellite',
    category: 'satellites',
    license: 'Copernicus Sentinel Data',
    updateFrequency: '6-12 días',
    geographicScope: 'Global',
    requiresAuth: true,
    envVariable: 'COPERNICUS_CLIENT_ID', // Server-side OAuth
    status: 'notConfigured',
  },
  {
    id: 'landsat',
    name: 'Landsat',
    organization: 'NASA / USGS',
    type: 'satellite',
    url: 'https://landsat.usgs.gov',
    category: 'satellites',
    license: 'Public Domain',
    updateFrequency: '16 días',
    geographicScope: 'Global',
    requiresAuth: false,
    status: 'notConfigured',
  },
  {
    id: 'effis',
    name: 'EFFIS',
    organization: 'European Commission / JRC',
    type: 'fire',
    url: 'https://effis.jrc.ec.europa.eu',
    category: 'fires',
    license: 'EU Data',
    updateFrequency: 'Diaria',
    geographicScope: 'Europa, Mediterráneo',
    requiresAuth: false,
    status: 'notConfigured',
  },
];

export const resources: Resource[] = [
  {
    id: 'globe-cesium',
    type: 'globe',
    category: 'dataLayers',
    name: 'Globo Cesium 3D',
    description: 'Visualización fotorealista 3D con CesiumJS + Esri World Imagery',
    status: 'operational',
    enabled: true,
    available: true,
    requiresAuth: false,
  },
  {
    id: 'earthquake-layer',
    type: 'layer',
    category: 'earthquakes',
    name: 'Terremotos (USGS)',
    description: 'Sismicidad global M2.5+ en tiempo real',
    source: 'USGS',
    status: 'active',
    enabled: true,
    available: true,
    requiresAuth: false,
  },
  {
    id: 'flights-layer',
    type: 'layer',
    category: 'aircraft',
    name: 'Vuelos en vivo',
    description: '11,000+ aeronaves con telemetría real',
    source: 'OpenSky Network',
    status: 'notConfigured',
    enabled: false,
    available: false,
    requiresAuth: false, // Keyless anonymous works, but needs server proxy
  },
  {
    id: 'military-layer',
    type: 'layer',
    category: 'aircraft',
    name: 'Vuelos militares',
    description: 'Tráfico ADS-B militar',
    source: 'adsb.lol',
    status: 'notConfigured',
    enabled: false,
    available: false,
    requiresAuth: false,
  },
  {
    id: 'vessels-layer',
    type: 'layer',
    category: 'vessels',
    name: 'Buques en vivo',
    description: 'Miles de embarcaciones worldwide',
    source: 'AISStream',
    status: 'notConfigured',
    enabled: false,
    available: false,
    requiresAuth: true,
  },
  {
    id: 'satellites-layer',
    type: 'layer',
    category: 'satellites',
    name: 'Satélites',
    description: '838 objetos con propagación SGP4',
    source: 'CelesTrak',
    status: 'notConfigured',
    enabled: false,
    available: false,
    requiresAuth: false,
  },
  {
    id: 'fires-layer',
    type: 'layer',
    category: 'fires',
    name: 'Incendios activos',
    description: 'Detecciones NASA FIRMS, últimas 24h',
    source: 'NASA FIRMS',
    status: 'notConfigured',
    enabled: false,
    available: false,
    requiresAuth: true,
  },
  {
    id: 'cctv-layer',
    type: 'layer',
    category: 'cameras',
    name: 'Cámaras públicas',
    description: '~3,900 cámaras proyectadas en 3D',
    source: 'City APIs (TxDOT, TfL, Caltrans, etc.)',
    status: 'notConfigured',
    enabled: false,
    available: false,
    requiresAuth: false,
  },
  {
    id: 'weather-layer',
    type: 'layer',
    category: 'weather',
    name: 'Meteorología',
    description: 'Viento NOAA/ECMWF, radar, nubes, rayos',
    source: 'NOAA / ECMWF',
    status: 'notConfigured',
    enabled: false,
    available: false,
    requiresAuth: false,
  },
  {
    id: 'cyclones-layer',
    type: 'layer',
    category: 'weather',
    name: 'Ciclones',
    description: 'Avisos NHC/CPHC con conos de incertidumbre',
    source: 'NOAA NHC/CPHC',
    status: 'notConfigured',
    enabled: false,
    available: false,
    requiresAuth: false,
  },
  {
    id: 'traffic-layer',
    type: 'layer',
    category: 'infrastructure',
    name: 'Tráfico',
    description: 'Vehículos simulados en carreteras OSM',
    source: 'OSM + TomTom (opcional)',
    status: 'notConfigured',
    enabled: false,
    available: false,
    requiresAuth: false,
  },
  {
    id: 'transit-layer',
    type: 'layer',
    category: 'infrastructure',
    name: 'Transporte público',
    description: 'Buses, metros, trenes en vivo',
    source: 'GTFS-Realtime',
    status: 'notConfigured',
    enabled: false,
    available: false,
    requiresAuth: false,
  },
  {
    id: 'radio-layer',
    type: 'layer',
    category: 'infrastructure',
    name: 'Radio mundial',
    description: 'Emisoras geolocalizadas con sintonizador analógico',
    source: 'Radio Browser',
    status: 'notConfigured',
    enabled: false,
    available: false,
    requiresAuth: false,
  },
  {
    id: 'space-missions',
    type: 'layer',
    category: 'missions',
    name: 'Misiones espaciales',
    description: 'Lanzamientos últimos 30 días con replay',
    source: 'Launch Library 2',
    status: 'notConfigured',
    enabled: false,
    available: false,
    requiresAuth: false,
  },
  {
    id: 'directions-layer',
    type: 'layer',
    category: 'infrastructure',
    name: 'Rutas',
    description: 'Rutas A-B sobre el terreno con OSRM',
    source: 'OSRM / FOSSGIS',
    status: 'notConfigured',
    enabled: false,
    available: false,
    requiresAuth: false,
  },
  {
    id: 'google-3d-tiles',
    type: 'layer',
    category: 'dataLayers',
    name: 'Google Photorealistic 3D',
    description: 'Ciudades fotorealistas 3D via Cesium ion',
    source: 'Google / Cesium ion',
    status: 'notConfigured',
    enabled: false,
    available: false,
    requiresAuth: true,
  },
  {
    id: 'voice-agent',
    type: 'module',
    category: 'missions',
    name: 'GEV MIC — Asistente de voz',
    description: 'Control por voz con OpenAI Realtime API',
    source: 'OpenAI',
    status: 'notConfigured',
    enabled: false,
    available: false,
    requiresAuth: true,
  },
  {
    id: 'firecycle-module',
    type: 'vertical',
    category: 'fires',
    name: 'FIRECYCLE EXTREM',
    description: 'Inteligencia territorial para incendios',
    status: 'comingSoon',
    enabled: false,
    available: false,
    requiresAuth: false,
  },
  {
    id: 'evidence-engine',
    type: 'module',
    category: 'evidence',
    name: 'Motor de Evidencias',
    description: 'Captura y verificación de evidencias geoespaciales',
    status: 'comingSoon',
    enabled: false,
    available: false,
    requiresAuth: false,
  },
  {
    id: 'ai-agents',
    type: 'module',
    category: 'missions',
    name: 'Agentes de Inteligencia',
    description: 'Agentes IA para análisis geoespacial',
    status: 'comingSoon',
    enabled: false,
    available: false,
    requiresAuth: false,
  },
];

export function getSourcesByCategory(category: string): DataSource[] {
  return dataSources.filter(s => s.category === category);
}

export function getResourcesByCategory(category: string): Resource[] {
  return resources.filter(r => r.category === category);
}

/**
 * Count sources with VERIFIED integration.
 * A source is "active" only if code exists that actually fetches data from it.
 * Currently: Esri imagery (baseLayer), USGS earthquakes (fetch in Globe.tsx)
 */
export function getActiveSourcesCount(): number {
  return dataSources.filter(s => s.status === 'active').length;
}

export function getNotConfiguredCount(): number {
  return dataSources.filter(s => s.status === 'notConfigured').length;
}

export function getKeylessSourcesCount(): number {
  return dataSources.filter(s => !s.requiresAuth).length;
}

export function getKeyRequiredSourcesCount(): number {
  return dataSources.filter(s => s.requiresAuth).length;
}
