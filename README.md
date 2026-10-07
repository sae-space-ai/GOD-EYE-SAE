# GOD EYE SAE

## Centro de Inteligencia Geoespacial

**Observación territorial · Análisis espacial · GEOINT**

---

## Descripción

GOD EYE SAE es una plataforma de inteligencia geoespacial que proporciona un centro de mando profesional para la observación de la Tierra, análisis territorial y herramientas de inteligencia espacial.

### Características Principales

- 🌍 **Globo 3D interactivo** con visualización WebGL (Three.js)
- 🇪🇸 **Interfaz completa en español** (es-ES) con soporte para inglés (en-US)
- 📊 **Catálogo visible de recursos** con estados en tiempo real
- 🔍 **Inspector contextual** para entidades seleccionadas
- 🎯 **Selector de modo operacional** (EO, OSINT, FIRECYCLE, Evidencias, IA)
- 📡 **Registro de fuentes de datos** con estados honestos
- 🔒 **Seguridad**: sin claves API en el frontend

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

| Variable | Descripción | Estado |
|----------|-------------|--------|
| `VITE_FIRMS_API_KEY` | API key de NASA FIRMS | No configurada |
| `VITE_COPERNICUS_API_KEY` | API key de Copernicus | No configurada |

## Arquitectura

Ver [docs/GOD_EYE_SAE_ARCHITECTURE.md](docs/GOD_EYE_SAE_ARCHITECTURE.md)

## Módulos

### Estado Actual

| Módulo | Estado | Descripción |
|--------|--------|-------------|
| Globo 3D | ✅ Operativo | Visualización WebGL con Three.js |
| Interfaz española | ✅ Operativo | i18n completo es-ES / en-US |
| Catálogo de recursos | ✅ Operativo | Panel izquierdo con todos los recursos |
| Inspector contextual | ✅ Operativo | Panel derecho con contexto |
| Centro de misión | ✅ Operativo | Selector de entorno de trabajo |
| NASA FIRMS | ⚠️ No configurado | Requiere API key |
| USGS Earthquakes | ✅ Activo | Datos sísmicos públicos |
| Copernicus | ⚠️ No configurado | Requiere API key |
| FIRECYCLE EXTREM | 🔜 Próximamente | Arquitectura preparada |
| Evidence Engine | 🔜 Próximamente | Modelo definido |
| Agentes IA | 🔜 Próximamente | Contratos preparados |

### FIRECYCLE EXTREM

Vertical especializado en inteligencia territorial para incendios. Ver [docs/FIRECYCLE_INTEGRATION.md](docs/FIRECYCLE_INTEGRATION.md).

### Evidence Engine

Motor de evidencias para captura y verificación de datos geoespaciales.

### Agentes de Inteligencia

Sistema de agentes IA con ciclo: Observar → Detectar → Contrastar → Analizar → Proponer → Aprobar → Ejecutar → Documentar.

## Fuentes de Datos

Ver [docs/DATA_SOURCE_REGISTRY.md](docs/DATA_SOURCE_REGISTRY.md)

## Inventario de Recursos

Ver [docs/RESOURCE_INVENTORY.md](docs/RESOURCE_INVENTORY.md)

## Internacionalización

Ver [docs/I18N.md](docs/I18N.md)

## Seguridad

- No se almacenan claves API en el código fuente
- Las variables `VITE_*` se inyectan en tiempo de build
- Los permisos de micrófono y geolocalización requieren acción explícita del usuario
- No se exponen secretos en el frontend

## Despliegue

### Vercel

La aplicación es compatible con Vercel como SPA estática:

```
Build command: npm run build
Output directory: dist
```

## Stack Técnico

- React 18 + TypeScript
- Vite 6
- Tailwind CSS 4
- Three.js (globo 3D)
- Lucide React (iconos)
- Framer Motion (animaciones)
- date-fns (fechas)

## Licencia

Consultar los archivos de licencia del proyecto original.

---

*GOD EYE SAE — Centro de Inteligencia Geoespacial*
