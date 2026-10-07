# GOD EYE SAE — Arquitectura Backend

## Visión General

GOD EYE SAE utiliza una arquitectura híbrida:
- **Frontend**: React 18 + Vite + TypeScript + CesiumJS (SPA)
- **Backend**: Vercel Serverless Functions (/api/*)
- **Persistencia local**: IndexedDB (Evidence Engine + Audit Events)

## Estructura

```
api/
├── health.ts        # GET /api/health — Estado del sistema
├── earthquakes.ts   # GET /api/earthquakes — Proxy USGS con caché
├── satellites.ts    # GET /api/satellites — Proxy CelesTrak TLE
├── flights.ts       # GET /api/flights — Proxy OpenSky
└── fires.ts         # GET /api/fires — Proxy NASA FIRMS (requiere FIRMS_MAP_KEY)
```

## Endpoints

### GET /api/health
Retorna estado del sistema sin operaciones costosas.

```json
{
  "status": "operational",
  "version": "2.0.0",
  "timestamp": "2026-...",
  "environment": "production",
  "services": {
    "frontend": "operational",
    "cesium": "operational",
    "usgs": "operational",
    "celestrak": "operational",
    "opensky": "operational",
    "nasaFirms": "configured|not_configured",
    "aisstream": "configured|not_configured"
  }
}
```

### GET /api/earthquakes
Proxy de USGS con caché de 1 minuto.

### GET /api/satellites
Proxy de CelesTrak TLE con caché de 5 minutos.

### GET /api/flights
Proxy de OpenSky con caché de 15 segundos (respetando rate limits).

### GET /api/fires
Proxy de NASA FIRMS. Requiere `FIRMS_MAP_KEY` en el servidor.

## Seguridad

- Las claves API privadas NUNCA se exponen al navegador
- FIRMS_MAP_KEY solo existe en el servidor
- CORS configurado por endpoint
- X-Content-Type-Options: nosniff en /api/*
- Sin stack traces en respuestas de error

## Vercel Configuration

```json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "/api/$1" },
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

El rewrite de SPA excluye /api/* para que las funciones serverless funcionen correctamente.

## Caché

| Fuente | TTL | Razón |
|--------|-----|-------|
| USGS | 60s | Datos sísmicos cambian rápidamente |
| CelesTrak | 300s | TLE actualizado diariamente |
| OpenSky | 15s | Rate limits estrictos |
| NASA FIRMS | 180s | Actualización cada 3-6h |

## Limitaciones

- Vercel Functions son stateless (caché en memoria es por-invocación)
- Para caché persistente se necesitaría Vercel KV o Redis externo
- WebSocket persistente (AISStream) NO es compatible con Vercel Functions
- Para AISStream se necesita un servicio persistente externo
