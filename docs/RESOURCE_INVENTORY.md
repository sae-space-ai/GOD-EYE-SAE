# GOD EYE SAE — Inventario de Recursos

## Recursos Operativos

| ID | Nombre | Categoría | Estado | Fuente |
|---|---|---|---|---|
| globe-3d | Globo 3D | Capas de datos | Operativo | Three.js |
| earthquake-layer | Terremotos (USGS) | Terremotos | Activo | USGS |
| openstreetmap | OpenStreetMap | Capas de datos | Activo | OSM Foundation |
| esri-imagery | Esri World Imagery | Capas de datos | Activo | Esri |

## Recursos No Configurados (requieren variable de entorno)

| ID | Nombre | Categoría | Variable necesaria |
|---|---|---|---|
| fires-layer | Incendios (NASA FIRMS) | Incendios | VITE_FIRMS_API_KEY |
| aircraft-layer | Aeronaves | Aeronaves | Sin definir |
| vessels-layer | Buques | Buques | Sin definir |

## Recursos Próximamente

| ID | Nombre | Categoría | Descripción |
|---|---|---|---|
| satellite-tracks | Órbitas satelitales | Satélites | Posiciones orbitales |
| weather-layer | Meteorología | Meteorología | Capas meteorológicas |
| firecycle-module | FIRECYCLE EXTREM | Incendios | Inteligencia territorial |
| evidence-engine | Motor de Evidencias | Evidencias | Captura y verificación |
| ai-agents | Agentes de Inteligencia | Misiones | Análisis geoespacial IA |

## Fuentes de Datos Registradas

| ID | Nombre | Organización | Estado | Ámbito |
|---|---|---|---|---|
| nasa-firms | NASA FIRMS | NASA | No configurado | Global |
| usgs-earthquakes | USGS | USGS | Activo | Global |
| effis | EFFIS | EC / JRC | No configurado | Europa |
| copernicus | Copernicus | ESA / EU | No configurado | Global |
| sentinel-2 | Sentinel-2 | ESA | No configurado | Global |
| sentinel-1 | Sentinel-1 | ESA | No configurado | Global |
| landsat | Landsat | NASA / USGS | No configurado | Global |
| openstreetmap | OpenStreetMap | OSM Foundation | Activo | Global |
| esri-imagery | Esri World Imagery | Esri | Activo | Global |

## Estados Normalizados

- **ACTIVO**: Funcional y conectado
- **INACTIVO**: Disponible pero desactivado
- **NO CONFIGURADO**: Requiere variable de entorno o API key
- **NO DISPONIBLE**: No puede funcionar en el entorno actual
- **ERROR**: Fallo en la conexión o servicio
- **CARGANDO**: En proceso de inicialización
- **EXPERIMENTAL**: Funcionalidad en pruebas
- **PRÓXIMAMENTE**: Planificado pero no implementado
