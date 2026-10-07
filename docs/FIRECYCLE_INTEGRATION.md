# GOD EYE SAE — FIRECYCLE EXTREM

## Descripción

FIRECYCLE EXTREM es un vertical especializado de GOD EYE SAE dedicado a la inteligencia territorial para incendios forestales.

## Estado Actual

**Arquitectura preparada. Módulos no conectados.**

FIRECYCLE está definido como un módulo vertical que comparte el núcleo de GOD EYE SAE (globo, fuentes, interfaz). No sustituye al núcleo.

## Módulos Planificados

### Observación de la Tierra
- **Sentinel-2 L2A**: Imágenes multiespectrales para análisis de vegetación y severidad
- **Sentinel-1**: Radar para detección de áreas quemadas independientemente de nubes
- **Landsat**: Series temporales largas para análisis histórico

### Detección y Monitoreo
- **NASA FIRMS**: Puntos calientes activos (requiere API key)
- **EFFIS**: Información europea sobre incendios forestales

### Índices de Severidad
- **NBR** (Normalized Burn Ratio)
- **dNBR** (differenced NBR)
- **RdNBR** (Relativized dNBR)

### Análisis Territorial
- Perímetros de incendio
- Puntos calientes
- Evaluación de severidad
- Vegetación y usos del suelo
- Parcelas y municipios
- Infraestructuras afectadas
- Hidrografía
- Pendiente y orientación

### Meteorología
- Condiciones meteorológicas
- Predicción de comportamiento del fuego
- Series temporales

## Territorio Piloto

Ámbito de demostración propuesto:
- Extremadura
- Cáceres
- Las Hurdes
- Pinofranqueado
- Caminomorro
- Nuñomoral

**Nota**: El piloto de 100 hectáreas se trata como propuesta mientras no exista evidencia oficial de autorización.

## Próximos Pasos

1. Configurar acceso a Copernicus Browser / API
2. Obtener API key de NASA FIRMS
3. Implementar adapter para Sentinel-2 L2A
4. Desarrollar cálculo de índices NBR
5. Integrar perímetros de incendio
6. Conectar series temporales

## Estructura de Código

```
src/
├── verticals/
│   └── firecycle/
│       ├── index.ts          # Punto de entrada del vertical
│       ├── adapters/         # Adapters para fuentes de datos
│       ├── indices/          # Cálculo de índices (NBR, dNBR)
│       ├── components/       # Componentes específicos
│       └── types.ts          # Tipos específicos
```

Esta estructura está preparada pero no implementada.
