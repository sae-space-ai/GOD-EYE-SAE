"""
SAE Core Evidence Engine - Evidence contracts and provenance.

This module defines evidence capture, provenance tracking, and integrity verification.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field
import hashlib
import json
from ..common.enums import generate_id, utc_now


# ============================================================================
# PROVENANCE
# ============================================================================

@dataclass
class Provenance:
    """Provenance tracking for evidence."""
    source_id: str
    source_name: str
    source_reference: Optional[str] = None
    source_timestamp: Optional[datetime] = None
    retrieved_at: datetime = field(default_factory=utc_now)
    dataset: Optional[str] = None
    dataset_version: Optional[str] = None
    processing_steps: List[str] = field(default_factory=list)
    model_id: Optional[str] = None
    model_version: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    software_version: str = "1.0.0"


# ============================================================================
# EVIDENCE
# ============================================================================

@dataclass
class Evidence:
    """Evidence record with integrity hash."""
    id: str
    mission_id: str
    source_id: str
    entity_id: str
    entity_type: str
    captured_at: datetime
    source_timestamp: datetime
    coordinates: Dict[str, float]  # {"latitude": ..., "longitude": ..., "altitude": ...}
    geometry: Optional[Dict[str, Any]] = None  # GeoJSON geometry
    source_url: Optional[str] = None
    source_type: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: Optional[float] = None
    status: str = "captured"  # "captured", "verified", "rejected", "pending", "superseded"
    hash: str = ""  # SHA-256 hash
    snapshot: str = ""  # JSON snapshot of entity
    provenance: Provenance = field(default_factory=lambda: Provenance(source_id="", source_name=""))
    
    def compute_hash(self) -> str:
        """Compute SHA-256 hash of evidence content."""
        content = {
            "source_id": self.source_id,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "source_timestamp": self.source_timestamp.isoformat(),
            "coordinates": self.coordinates,
            "source_url": self.source_url,
            "source_type": self.source_type,
            "metadata": self.metadata,
            "snapshot": self.snapshot,
        }
        canonical = json.dumps(content, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()
    
    def verify_integrity(self) -> bool:
        """Verify evidence integrity against hash."""
        if not self.hash:
            return False
        computed = self.compute_hash()
        return computed == self.hash


# ============================================================================
# EVIDENCE CAPTURE
# ============================================================================

class EvidenceCapture:
    """
    Captures evidence from entities and observations.
    
    Ensures:
    - Provenance tracking
    - Integrity hashing (SHA-256)
    - Status management
    """
    
    def capture(
        self,
        mission_id: str,
        entity: Dict[str, Any],
        source_id: str,
        source_name: str
    ) -> Evidence:
        """Capture evidence from entity."""
        # Extract coordinates
        coordinates = entity.get("position", {})
        if not coordinates:
            coordinates = entity.get("coordinates", {})
        
        # Create snapshot
        snapshot = json.dumps(entity, sort_keys=True)
        
        # Create provenance
        provenance = Provenance(
            source_id=source_id,
            source_name=source_name,
            source_reference=entity.get("id"),
            source_timestamp=datetime.fromisoformat(entity.get("timestamp", utc_now().isoformat())),
            retrieved_at=utc_now()
        )
        
        # Create evidence
        evidence = Evidence(
            id=generate_id(),
            mission_id=mission_id,
            source_id=source_id,
            entity_id=entity.get("id", generate_id()),
            entity_type=entity.get("type", "unknown"),
            captured_at=utc_now(),
            source_timestamp=provenance.source_timestamp,
            coordinates=coordinates,
            source_url=entity.get("provenance", {}).get("sourceUrl"),
            source_type=source_id,
            metadata=entity.get("properties", {}),
            snapshot=snapshot,
            provenance=provenance
        )
        
        # Compute hash
        evidence.hash = evidence.compute_hash()
        
        return evidence


# ============================================================================
# EVIDENCE VERIFICATION
# ============================================================================

class EvidenceVerification:
    """
    Verifies evidence integrity and status.
    """
    
    def verify(self, evidence: Evidence) -> bool:
        """Verify evidence integrity."""
        return evidence.verify_integrity()
    
    def mark_verified(self, evidence: Evidence) -> None:
        """Mark evidence as verified."""
        if not evidence.verify_integrity():
            raise ValueError("Cannot verify evidence with invalid integrity")
        evidence.status = "verified"
    
    def mark_rejected(self, evidence: Evidence, reason: str) -> None:
        """Mark evidence as rejected."""
        evidence.status = "rejected"
        evidence.metadata["rejection_reason"] = reason
