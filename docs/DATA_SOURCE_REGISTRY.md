# GOD EYE SAE — Registro de Fuentes de Datos

## Fuentes Activas

### USGS Earthquakes
- **Organización**: United States Geological Survey
- **Tipo**: Datos sísmicos
- **URL**: https://earthquake.usgs.gov/fdsnws/event/1/
- **Licencia**: Public Domain
- **Frecuencia**: Tiempo real
- **Ámbito**: Global
- **Autenticación**: No requerida
- **Estado**: ACTIVO

### OpenStreetMap
- **Organización**: OSM Foundation
- **Tipo**: Mapa base
- **URL**: https://www.openstreetmap.org
- **Licencia**: ODbL
- **Frecuencia**: Continua
- **Ámbito**: Global
- **Autenticación**: No requerida
- **Estado**: ACTIVO

### Esri World Imagery
- **Organización**: Esri
- **Tipo**: Mapa base (imagen satelital)
- **URL**: https://www.esri.com
- **Licencia**: Esri Terms
- **Frecuencia**: Variable
- **Ámbito**: Global
- **Autenticación**: No requerida
- **Estado**: ACTIVO

## Fuentes No Configuradas

### NASA FIRMS
- **Organización**: NASA
- **Tipo**: Incendios / Puntos calientes
- **URL**: https://firms.modaps.eosdis.nasa.gov
- **Licencia**: Public
- **Frecuencia**: Cada 3-6 horas
- **Ámbito**: Global
- **Variable de entorno**: `VITE_FIRMS_API_KEY`
- **Estado**: NO CONFIGURADO

### EFFIS
- **Organización**: European Commission / JRC
- **Tipo**: Incendios forestales
- **URL**: https://effis.jrc.ec.europa.eu
- **Licencia**: EU Data
- **Frecuencia**: Diaria
- **Ámbito**: Europa, Mediterráneo
- **Autenticación**: No requerida (acceso web)
- **Estado**: NO CONFIGURADO

### Copernicus
- **Organización**: ESA / EU
- **Tipo**: Observación de la Tierra
- **URL**: https://copernicus.eu
- **Licencia**: Copernicus Sentinel Data
- **Frecuencia**: Variable
- **Ámbito**: Global
- **Variable de entorno**: `VITE_COPERNICUS_API_KEY`
- **Estado**: NO CONFIGURADO

### Sentinel-2
- **Organización**: ESA
- **Tipo**: Satélite multiespectral
- **Licencia**: Copernicus Sentinel Data
- **Frecuencia**: 5 días (revisita)
- **Ámbito**: Global
- **Variable de entorno**: `VITE_COPERNICUS_API_KEY`
- **Estado**: NO CONFIGURADO

### Sentinel-1
- **Organización**: ESA
- **Tipo**: Satélite radar (SAR)
- **Licencia**: Copernicus Sentinel Data
- **Frecuencia**: 6-12 días
- **Ámbito**: Global
- **Variable de entorno**: `VITE_COPERNICUS_API_KEY`
- **Estado**: NO CONFIGURADO

### Landsat
- **Organización**: NASA / USGS
- **Tipo**: Satélite de observación terrestre
- **URL**: https://landsat.usgs.gov
- **Licencia**: Public Domain
- **Frecuencia**: 16 días
- **Ámbito**: Global
- **Autenticación**: No requerida
- **Estado**: NO CONFIGURADO

## Notas de Seguridad

- **Nunca** exponer claves API en el código fuente
- Las variables `VITE_*` se inyectan en tiempo de build
- Para producción, usar variables de entorno del servidor
- No almacenar secretos en el repositorio
- Respetar los términos de licencia de cada fuente
