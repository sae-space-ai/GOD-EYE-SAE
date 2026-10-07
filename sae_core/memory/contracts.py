"""
SAE Core Memory Engine - Memory contracts and interfaces.

This module defines the memory system contracts for working, mission,
spatial, temporal, semantic, and evidence memory.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field
from ..common.enums import generate_id, utc_now


# ============================================================================
# WORKING MEMORY
# ============================================================================

@dataclass
class WorkingMemory:
    """
    Ephemeral context for current mission execution.
    
    Not persisted automatically. Cleared after mission completion.
    """
    mission_id: str
    current_step: Optional[str] = None
    selected_entities: List[str] = field(default_factory=list)
    observations: List[Dict[str, Any]] = field(default_factory=list)
    intermediate_results: Dict[str, Any] = field(default_factory=dict)
    tool_results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=utc_now)
    
    def clear(self) -> None:
        """Clear working memory."""
        self.current_step = None
        self.selected_entities.clear()
        self.observations.clear()
        self.intermediate_results.clear()
        self.tool_results.clear()
        self.errors.clear()


# ============================================================================
# MISSION MEMORY
# ============================================================================

@dataclass
class MissionMemory:
    """
    Persistent memory for mission lifecycle.
    
    Stores mission state, plans, execution history, decisions, results.
    """
    mission_id: str
    mission_state: Dict[str, Any] = field(default_factory=dict)
    plans: List[Dict[str, Any]] = field(default_factory=list)
    execution_history: List[Dict[str, Any]] = field(default_factory=list)
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    approvals: List[Dict[str, Any]] = field(default_factory=list)
    evidence_references: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


# ============================================================================
# SPATIAL MEMORY INTERFACE
# ============================================================================

class SpatialMemory:
    """
    Interface for spatial memory operations.
    
    Supports queries by:
    - Coordinates
    - Bounding box
    - Polygon
    - Tile
    - CRS
    """
    
    def query_by_bbox(self, bbox: List[float], crs: str = "EPSG:4326") -> List[Dict[str, Any]]:
        """Query observations by bounding box."""
        raise NotImplementedError("SpatialMemory.query_by_bbox() not implemented")
    
    def query_by_polygon(self, polygon: List[List[float]], crs: str = "EPSG:4326") -> List[Dict[str, Any]]:
        """Query observations by polygon."""
        raise NotImplementedError("SpatialMemory.query_by_polygon() not implemented")
    
    def store_observation(self, observation: Dict[str, Any]) -> None:
        """Store spatial observation."""
        raise NotImplementedError("SpatialMemory.store_observation() not implemented")


# ============================================================================
# TEMPORAL MEMORY INTERFACE
# ============================================================================

class TemporalMemory:
    """
    Interface for temporal memory operations.
    
    Distinguishes:
    - event_time: When event occurred
    - acquisition_time: When data was acquired
    - ingestion_time: When data was ingested
    """
    
    def query_history(self, start: datetime, end: datetime) -> List[Dict[str, Any]]:
        """Query observations between time range."""
        raise NotImplementedError("TemporalMemory.query_history() not implemented")
    
    def get_latest_observation(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get latest observation for entity."""
        raise NotImplementedError("TemporalMemory.get_latest_observation() not implemented")
    
    def get_change_history(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get change history for entity."""
        raise NotImplementedError("TemporalMemory.get_change_history() not implemented")


# ============================================================================
# SEMANTIC MEMORY INTERFACE
# ============================================================================

@dataclass
class SemanticMemoryEntry:
    """Entry in semantic memory."""
    id: str
    embedding: List[float]  # Vector embedding
    model_version: str
    source: str
    mission_id: Optional[str]
    entity_id: Optional[str]
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class VectorStore:
    """
    Interface for vector store operations.
    
    Decoupled from specific providers (Pinecone, Weaviate, Milvus, etc.)
    """
    
    def upsert(self, entries: List[SemanticMemoryEntry]) -> None:
        """Insert or update entries."""
        raise NotImplementedError("VectorStore.upsert() not implemented")
    
    def search(self, query_embedding: List[float], top_k: int = 10) -> List[SemanticMemoryEntry]:
        """Search for similar entries."""
        raise NotImplementedError("VectorStore.search() not implemented")
    
    def delete(self, entry_ids: List[str]) -> None:
        """Delete entries by ID."""
        raise NotImplementedError("VectorStore.delete() not implemented")
    
    def health(self) -> Dict[str, Any]:
        """Check vector store health."""
        raise NotImplementedError("VectorStore.health() not implemented")


class SemanticMemory:
    """
    Semantic memory using vector embeddings.
    
    References embeddings, model versions, sources, missions, entities.
    """
    
    def __init__(self, vector_store: VectorStore):
        """Initialize with vector store."""
        self.vector_store = vector_store
    
    def store(self, entry: SemanticMemoryEntry) -> None:
        """Store semantic memory entry."""
        self.vector_store.upsert([entry])
    
    def search(self, query: List[float], top_k: int = 10) -> List[SemanticMemoryEntry]:
        """Search semantic memory."""
        return self.vector_store.search(query, top_k)


# ============================================================================
# EVIDENCE MEMORY
# ============================================================================

class EvidenceMemory:
    """
    Memory for evidence references.
    
    Only stores references to Evidence Engine, not the evidence itself.
    """
    
    def __init__(self):
        """Initialize evidence memory."""
        self.references: Dict[str, List[str]] = {}  # mission_id -> [evidence_ids]
    
    def add_reference(self, mission_id: str, evidence_id: str) -> None:
        """Add evidence reference for mission."""
        if mission_id not in self.references:
            self.references[mission_id] = []
        self.references[mission_id].append(evidence_id)
    
    def get_references(self, mission_id: str) -> List[str]:
        """Get evidence references for mission."""
        return self.references.get(mission_id, [])


# ============================================================================
# SPATIOTEMPORAL MEMORY
# ============================================================================

@dataclass
class SpatiotemporalEntry:
    """Spatiotemporal memory entry."""
    id: str
    geometry: Dict[str, Any]  # GeoJSON geometry
    time: datetime
    source: str
    modality: str  # "sar", "lidar", "optical", etc.
    latent_representation: Optional[List[float]] = None  # From foundation model
    metadata: Dict[str, Any] = field(default_factory=dict)


class SpatiotemporalMemory:
    """
    Memory for spatiotemporal observations.
    
    Relates geometry, time, source, modality, latent representation.
    """
    
    def __init__(self):
        """Initialize spatiotemporal memory."""
        self.entries: Dict[str, SpatiotemporalEntry] = {}
    
    def store(self, entry: SpatiotemporalEntry) -> None:
        """Store spatiotemporal entry."""
        self.entries[entry.id] = entry
    
    def query_by_time_range(self, start: datetime, end: datetime) -> List[SpatiotemporalEntry]:
        """Query entries by time range."""
        return [
            entry for entry in self.entries.values()
            if start <= entry.time <= end
        ]
    
    def query_by_modality(self, modality: str) -> List[SpatiotemporalEntry]:
        """Query entries by modality."""
        return [
            entry for entry in self.entries.values()
            if entry.modality == modality
        ]
