# GOD EYE SAE — Evidence Engine

## Visión General

El Motor de Evidencias captura, persiste y verifica evidencias geoespaciales con hash de integridad SHA-256.

## Estado

**IMPLEMENTADO Y FUNCIONAL**

- ✅ Captura de evidencias desde entidades Cesium
- ✅ Persistencia en IndexedDB
- ✅ Hash SHA-256 via Web Crypto API
- ✅ Verificación de integridad
- ✅ Exportación JSON
- ✅ Gestión de estados

## Modelo de Datos

```typescript
interface Evidence {
  id: string;
  missionId?: string;
  sourceId: string;
  entityId: string;
  entityType: string;
  capturedAt: string;
  sourceTimestamp: string;
  coordinates: {
    latitude: number;
    longitude: number;
    altitude?: number;
  };
  sourceUrl?: string;
  sourceType: string;
  metadata: Record<string, any>;
  confidence?: number;
  status: EvidenceStatus;
  hash: string;
  snapshot: string; // JSON de la entidad al capturar
}
```

## Estados

| Estado | Descripción |
|--------|-------------|
| CAPTURADA | Estado inicial tras captura |
| VERIFICADA | Requiere acción específica de verificación |
| RECHAZADA | Evidencia descartada |
| PENDIENTE | En proceso de revisión |
| SUPERADA | Reemplazada por evidencia más reciente |

## Hash de Integridad

- **Algoritmo**: SHA-256 (Web Crypto API)
- **Input**: Representación canónica JSON de la evidencia
- **Propósito**: Verificar que la evidencia no ha sido modificada
- **Nota**: No constituye cadena de custodia criptográfica completa

## API

```typescript
// Capturar evidencia
captureEvidence(entity: GeoEntity, missionId?: string): Promise<Evidence>

// Listar todas
listEvidence(): Promise<Evidence[]>

// Listar por fuente
listEvidenceBySource(sourceId: string): Promise<Evidence[]>

// Verificar integridad
verifyEvidence(evidence: Evidence): Promise<boolean>

// Actualizar estado
updateEvidenceStatus(id: string, status: EvidenceStatus): Promise<void>

// Exportar
exportEvidenceJSON(): Promise<string>
```

## Persistencia

- **Motor**: IndexedDB
- **Base de datos**: `god-eye-sae-evidence`
- **Stores**: evidence (con índices por sourceId, entityId, capturedAt, status)
- **Migración futura**: Diseñado para migrar a PostgreSQL cuando exista backend persistente

## Limitaciones

- IndexedDB es local al navegador
- No hay sincronización entre dispositivos
- Para evidencia compartida se necesita backend con base de datos
- El hash verifica integridad local, no constituye prueba legal
