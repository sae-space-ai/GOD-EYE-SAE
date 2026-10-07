# GOD EYE SAE

## Centro de Inteligencia Geoespacial

**Observación territorial · Análisis espacial · GEOINT**

---

## Upstream and Attribution

GOD EYE SAE se construye sobre el proyecto open-source **God's Eye View** de Bilawal Sidhu.

- **Repositorio upstream**: https://github.com/bilawalsidhu/gods-eye-view
- **Licencia upstream**: MIT
- **Motores**: CesiumJS, Esri World Imagery, Google Photorealistic 3D Tiles
- **Mantenedores upstream**: Bilawal Sidhu, Sameh Khamis (Halfpixel)

El código de GOD EYE SAE que transforma la interfaz (internacionalización, layout de centro de mando, Resource Explorer, Source Registry, Evidence Engine, FIRECYCLE) se licencia de forma compatible con MIT. Las atribuciones cartográficas y de datos se mantienen según los términos de cada proveedor.

**God's Eye View is © its original authors. GOD EYE SAE does not claim authorship over upstream code.**

---

## Descripción

GOD EYE SAE es una plataforma de inteligencia geoespacial que proporciona un centro de mando profesional para la observación de la Tierra, análisis territorial y herramientas de inteligencia espacial.

### Características Principales

- 🌍 **Globo 3D con CesiumJS** — Motor geoespacial real del upstream God's Eye View
- 🗺️ **Esri World Imagery** — Mapa base satelital sin clave (keyless)
- 🌐 **Terreno mundial** — Via Cesium ion (token básico incluido)
- 🇪🇸 **Interfaz completa en español** (es-ES) con soporte para inglés (en-US)
- 📊 **Catálogo visible de recursos** con estados honestos
- 🔍 **Inspector contextual** para entidades seleccionadas
- 🎯 **Selector de modo operacional** (EO, OSINT, FIRECYCLE, Evidencias, IA)
- 📡 **Registro de fuentes de datos** con estados verificados
- 🔒 **Seguridad**: claves API solo en servidor, nunca en el navegador

## Estado de Integración

### ✅ INTEGRADO Y VERIFICADO

| Componente | Estado | Detalle |
|------------|--------|---------|
| Globo CesiumJS | ✅ Funcional | Motor 3D real, Esri basemap, terreno |
| USGS Earthquakes | ✅ Funcional | Datos sísmicos M2.5+ en tiempo real (keyless) |
| Esri World Imagery | ✅ Funcional | Mapa base satelital (keyless) |
| Interfaz española | ✅ Funcional | i18n es-ES / en-US completo |
| Resource Explorer | ✅ Funcional | Panel izquierdo con todas las categorías |
| Context Inspector | ✅ Funcional | Panel derecho con contexto |
| Mission Launcher | ✅ Funcional | 6 entornos de trabajo |

### ⚠️ INTEGRADO EN UPSTREAM, REQUIERE SERVIDOR

Las siguientes capacidades existen en el upstream God's Eye View pero requieren el servidor Node.js del upstream para funcionar (proxy de APIs, WebSocket streams):

| Componente | Fuente upstream | Requiere |
|------------|-----------------|----------|
| Vuelos en vivo | OpenSky Network | Servidor proxy |
| Vuelos militares | adsb.lol | Servidor proxy |
| Buques en vivo | AISStream | Servidor proxy + API key |
| Satélites (SGP4) | CelesTrak | Integración de propagación |
| CCTV (~3,900 cámaras) | City APIs | Servidor proxy |
| Meteorología | NOAA/ECMWF | Integración de capas |
| Ciclones | NOAA NHC/CPHC | Integración de capas |
| Radio mundial | Radio Browser | Integración de audio |
| Rutas | OSRM | Integración de terreno |
| Misiones espaciales | Launch Library 2 | Integración de replay |
| Asistente de voz | OpenAI Realtime | Servidor + API key |
| Google 3D Tiles | Cesium ion / Google | Token + configuración |

### 🔜 ARQUITECTURA PREPARADA (no implementado)

| Componente | Estado |
|------------|--------|
| FIRECYCLE EXTREM | Vertical preparado, módulos no conectados |
| Evidence Engine | Modelo TypeScript completo, sin persistencia |
| Audit Events | Contrato definido, sin implementación |
| Agentes IA | Contratos preparados, sin conexión a modelos |

## Ejecución Local

```bash
# Instalar dependencias
npm install

# Desarrollo
npm run dev

# Build de producción
npm run build

# Verificación de tipos
npm run typecheck
```

## Variables de Entorno

Según el upstream, las claves API se gestionan en el SERVIDOR, no en el navegador:

| Variable | Uso | Lado |
|----------|-----|------|
| `FIRMS_MAP_KEY` | NASA FIRMS | Servidor |
| `AISSTREAM_API_KEY` | AISStream (buques) | Servidor |
| `OPENAI_API_KEY` | OpenAI Realtime (voz) | Servidor |
| `CESIUM_ION_TOKEN` | Cesium ion (3D Tiles) | Navegador (restringir) |
| `GOOGLE_MAPS_API_KEY` | Google 3D (metered) | Navegador (restringir) |
| `TOMTOM_API_KEY` | TomTom Traffic | Servidor |
| `COPERNICUS_CLIENT_ID` | Copernicus/Sentinel | Servidor (OAuth) |

**IMPORTANTE**: Las variables `VITE_*` se inyectan en el navegador y son accesibles públicamente. No usar `VITE_` para claves privadas.

## Arquitectura

```
src/
├── App.tsx              # Shell del centro de mando GOD EYE SAE
├── main.tsx             # Punto de entrada
├── index.css            # Estilos globales
├── components/
│   └── Globe.tsx        # Globo CesiumJS (motor upstream)
├── i18n/
│   ├── index.ts         # Sistema de internacionalización
│   └── locales/
│       ├── es-ES.ts     # Traducciones españolas
│       └── en-US.ts     # Traducciones inglesas
├── types/
│   └── index.ts         # Tipos TypeScript
└── data/
    └── sources.ts       # Registro de fuentes de datos
```

### Diferencias con el upstream

El upstream God's Eye View usa **Vanilla JavaScript** con CesiumJS directamente. GOD EYE SAE usa **React + TypeScript** como capa de interfaz sobre el mismo motor CesiumJS.

| Aspecto | Upstream (God's Eye View) | GOD EYE SAE |
|---------|---------------------------|-------------|
| Framework | Vanilla JS | React 18 + TypeScript |
| Motor 3D | CesiumJS | CesiumJS (mismo) |
| Mapa base | Esri World Imagery | Esri World Imagery (mismo) |
| Servidor | Node.js + Express | No incluido (requiere upstream) |
| Idioma | Inglés | Español (es-ES) predeterminado |
| Layout | Paneles propios | Centro de mando reorganizado |

## FIRECYCLE EXTREM

Vertical especializado en inteligencia territorial para incendios. Ver [docs/FIRECYCLE_INTEGRATION.md](docs/FIRECYCLE_INTEGRATION.md).

**Estado**: Arquitectura preparada. Módulos no conectados.

## Evidence Engine

Motor de evidencias para captura y verificación de datos geoespaciales.

**Estado**: Modelo TypeScript definido. Sin persistencia.

## Seguridad

- ✅ Sin claves API privadas en el frontend
- ✅ Variables de entorno de servidor para servicios autenticados
- ✅ Permisos de micrófono bajo control del usuario
- ✅ No se exponen secretos en el navegador
- ✅ Atribuciones cartográficas mantenidas

## Despliegue

### Vercel

La aplicación es compatible con Vercel como SPA estática:

```
Build command: npm run build
Output directory: dist
```

**Nota**: Para funcionalidades completas del upstream (vuelos, buques, CCTV, voz), se necesita el servidor Node.js del upstream God's Eye View.

## Stack Técnico

- React 18 + TypeScript
- Vite 6
- Tailwind CSS 4
- **CesiumJS** (motor geoespacial real del upstream)
- Lucide React (iconos)
- date-fns (fechas)

## Licencia

- **Código GOD EYE SAE**: MIT (compatible con upstream)
- **Código upstream God's Eye View**: MIT © Bilawal Sidhu
- **Datos**: Cada fuente tiene sus propios términos — ver [DATA_SOURCES upstream](https://github.com/bilawalsidhu/gods-eye-view/blob/main/DATA_SOURCES.md)
- **Mapas**: Esri Terms, OSM ODbL, Cesium ion Terms

---

*GOD EYE SAE — Centro de Inteligencia Geoespacial*
*Basado en God's Eye View por Bilawal Sidhu*
