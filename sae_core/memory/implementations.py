"""
SAE Core Memory - In-memory implementations.

This module provides in-memory implementations of memory interfaces
for development and testing. Production should use database-backed implementations.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from .contracts import (
    TemporalMemory,
    SpatialMemory,
    VectorStore,
    SemanticMemoryEntry,
    SpatiotemporalEntry,
)


class InMemoryTemporalMemory(TemporalMemory):
    """In-memory implementation of TemporalMemory."""
    
    def __init__(self):
        """Initialize temporal memory."""
        self.observations: List[Dict[str, Any]] = []
    
    def query_history(
        self,
        start: datetime,
        end: datetime,
        entity_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query observations between time range."""
        results = []
        for obs in self.observations:
            obs_time = obs.get("event_time") or obs.get("acquisition_time")
            if obs_time and start <= obs_time <= end:
                if entity_id is None or obs.get("entity_id") == entity_id:
                    results.append(obs)
        return sorted(results, key=lambda x: x.get("event_time", datetime.min))
    
    def get_latest_observation(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get latest observation for entity."""
        entity_obs = [
            obs for obs in self.observations
            if obs.get("entity_id") == entity_id
        ]
        if not entity_obs:
            return None
        return max(entity_obs, key=lambda x: x.get("event_time", datetime.min))
    
    def get_change_history(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get change history for entity."""
        return [
            obs for obs in self.observations
            if obs.get("entity_id") == entity_id and obs.get("type") == "change"
        ]
    
    def store_observation(self, observation: Dict[str, Any]) -> None:
        """Store observation."""
        self.observations.append(observation)


class InMemorySpatialMemory(SpatialMemory):
    """
    In-memory implementation of SpatialMemory.
    
    NOTE: This is a simplified implementation for development.
    Production should use PostGIS for real spatial queries.
    """
    
    def __init__(self):
        """Initialize spatial memory."""
        self.observations: List[Dict[str, Any]] = []
    
    def query_by_bbox(
        self,
        bbox: List[float],
        crs: str = "EPSG:4326"
    ) -> List[Dict[str, Any]]:
        """
        Query observations by bounding box.
        
        NOTE: This is a simplified implementation.
        Production should use PostGIS for accurate spatial queries.
        """
        if len(bbox) != 4:
            raise ValueError("BBox must have 4 values: [minx, miny, maxx, maxy]")
        
        minx, miny, maxx, maxy = bbox
        results = []
        
        for obs in self.observations:
            geom = obs.get("geometry", {})
            coords = geom.get("coordinates", [])
            
            if geom.get("type") == "Point" and len(coords) >= 2:
                lon, lat = coords[0], coords[1]
                if minx <= lon <= maxx and miny <= lat <= maxy:
                    results.append(obs)
        
        return results
    
    def query_by_polygon(
        self,
        polygon: List[List[float]],
        crs: str = "EPSG:4326"
    ) -> List[Dict[str, Any]]:
        """
        Query observations by polygon.
        
        NOTE: This is a simplified implementation.
        Production should use PostGIS for accurate spatial queries.
        """
        # Simplified: just return all observations
        # Production should use point-in-polygon algorithm
        return self.observations
    
    def store_observation(self, observation: Dict[str, Any]) -> None:
        """Store spatial observation."""
        self.observations.append(observation)


class InMemoryVectorStore(VectorStore):
    """
    In-memory implementation of VectorStore.
    
    NOTE: This is a simplified implementation for development.
    Production should use a real vector database (Pinecone, Weaviate, Milvus).
    """
    
    def __init__(self):
        """Initialize vector store."""
        self.entries: Dict[str, SemanticMemoryEntry] = {}
    
    def upsert(self, entries: List[SemanticMemoryEntry]) -> None:
        """Insert or update entries."""
        for entry in entries:
            self.entries[entry.id] = entry
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10
    ) -> List[SemanticMemoryEntry]:
        """
        Search for similar entries.
        
        NOTE: This uses simple cosine similarity.
        Production should use optimized vector search.
        """
        if not self.entries:
            return []
        
        # Calculate cosine similarity
        def cosine_similarity(a: List[float], b: List[float]) -> float:
            dot_product = sum(x * y for x, y in zip(a, b))
            norm_a = sum(x * x for x in a) ** 0.5
            norm_b = sum(x * x for x in b) ** 0.5
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return dot_product / (norm_a * norm_b)
        
        # Score all entries
        scored = []
        for entry in self.entries.values():
            score = cosine_similarity(query_embedding, entry.embedding)
            scored.append((score, entry))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Return top_k
        return [entry for _, entry in scored[:top_k]]
    
    def delete(self, entry_ids: List[str]) -> None:
        """Delete entries by ID."""
        for entry_id in entry_ids:
            if entry_id in self.entries:
                del self.entries[entry_id]
    
    def health(self) -> Dict[str, Any]:
        """Check vector store health."""
        return {
            "status": "healthy",
            "entries_count": len(self.entries),
            "implementation": "in-memory"
        }


class InMemorySpatiotemporalMemory:
    """
    In-memory implementation of SpatiotemporalMemory.
    
    NOTE: This is a simplified implementation for development.
    Production should use database with spatial and temporal indexing.
    """
    
    def __init__(self):
        """Initialize spatiotemporal memory."""
        self.entries: Dict[str, SpatiotemporalEntry] = {}
    
    def store(self, entry: SpatiotemporalEntry) -> None:
        """Store spatiotemporal entry."""
        self.entries[entry.id] = entry
    
    def query_by_time_range(
        self,
        start: datetime,
        end: datetime
    ) -> List[SpatiotemporalEntry]:
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
    
    def query_by_spatial_and_temporal(
        self,
        bbox: List[float],
        start: datetime,
        end: datetime
    ) -> List[SpatiotemporalEntry]:
        """Query entries by spatial and temporal range."""
        spatial_memory = InMemorySpatialMemory()
        spatial_memory.observations = [
            {"geometry": entry.geometry, "entry": entry}
            for entry in self.entries.values()
        ]
        
        spatial_results = spatial_memory.query_by_bbox(bbox)
        
        return [
            obs["entry"] for obs in spatial_results
            if start <= obs["entry"].time <= end
        ]
