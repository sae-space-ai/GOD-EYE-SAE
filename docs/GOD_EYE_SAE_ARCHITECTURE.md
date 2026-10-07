# GOD EYE SAE — Arquitectura

## Visión General

GOD EYE SAE es un Centro de Inteligencia Geoespacial que proporciona una interfaz profesional para la observación territorial, análisis espacial y herramientas GEOINT.

## Arquitectura Técnica

### Stack Frontend
- **Framework**: React 18 + TypeScript
- **Build**: Vite 6
- **Estilos**: Tailwind CSS 4
- **Globo 3D**: Three.js (WebGL)
- **Iconos**: Lucide React
- **Animaciones**: Framer Motion
- **Gráficos**: Recharts
- **Fechas**: date-fns

### Estructura de Directorios

```
src/
├── App.tsx              # Componente principal (shell de la aplicación)
├── main.tsx             # Punto de entrada
├── index.css            # Estilos globales
├── components/
│   └── Globe.tsx        # Globo 3D con Three.js
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

### Módulos Principales

1. **AppShell** (`App.tsx`): Layout principal con cabecera, paneles laterales, área central y barra inferior.
2. **Globe** (`Globe.tsx`): Visualización 3D de la Tierra con interacción.
3. **i18n**: Sistema centralizado de traducciones.
4. **ResourceExplorer**: Panel izquierdo con catálogo de recursos.
5. **ContextInspector**: Panel derecho con información contextual.
6. **MissionLauncher**: Modal de selección de entorno de trabajo.

### Internacionalización

- Idioma predeterminado: `es-ES`
- Idioma secundario: `en-US`
- Selector de idioma en la cabecera
- Persistencia en localStorage

### Modelo de Datos

- `Resource`: Representación uniforme de capas y funcionalidades.
- `DataSource`: Registro de fuentes externas.
- `SelectedEntity`: Entidad seleccionada en el globo.
- `Evidence`: Evidencia geoespacial (preparado para implementación futura).
- `AuditEvent`: Evento de auditoría (preparado para implementación futura).

## FIRECYCLE EXTREM

Vertical especializado preparado arquitectónicamente para:
- Análisis de severidad de incendios (NBR, dNBR, RdNBR)
- Integración con Sentinel-2, Sentinel-1, Landsat
- NASA FIRMS y EFFIS
- Perímetros, puntos calientes, vegetación
- Series temporales

Estado: Arquitectura preparada, módulos marcados como "Próximamente".

## Evidence Engine

Motor de evidencias preparado con modelo de datos completo:
- Captura, verificación, rechazo
- Hash y metadatos
- Vinculación a misiones y fuentes

Estado: Modelo definido, sin implementación funcional.

## Agentes IA

Contratos preparados para agentes de inteligencia espacial:
- Observar → Detectar → Contrastar → Analizar → Proponer → Aprobar → Ejecutar → Documentar
- Distinción entre hecho, dato, inferencia, hipótesis y recomendación

Estado: Interfaz preparada, sin conexión a modelos.

## Seguridad

- Sin claves API en el frontend
- Variables de entorno para servicios autenticados
- Permisos de micrófono/cámara bajo control del usuario
- Sin exposición de secretos

## Despliegue

- Compatible con Vercel (SPA estática)
- Build: `npm run build`
- Output: `dist/`
