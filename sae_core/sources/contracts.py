"""
SAE Core Sources - Source registry and adapter contracts.

This module defines the source registry and adapter interfaces
for data source management.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field
from ..common.enums import SourceStatus, generate_id, utc_now


# ============================================================================
# SOURCE CONTRACT
# ============================================================================

@dataclass
class SourceContract:
    """Data source definition and status."""
    id: str
    name: str
    category: str  # "earthquakes", "fires", "weather", etc.
    provider: str
    status: SourceStatus = SourceStatus.NOT_CONFIGURED
    configured: bool = False
    requires_auth: bool = False
    requires_server: bool = False
    last_fetch: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_error: Optional[str] = None
    refresh_interval: Optional[int] = None  # seconds
    provenance: str = ""
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# SOURCE ADAPTER INTERFACE
# ============================================================================

class SourceAdapter:
    """
    Interface for data source adapters.
    
    Each source must implement:
    - fetch_data(): Fetch data from source
    - normalize(): Normalize data to standard format
    - health(): Check source health
    """
    
    def __init__(self, source_id: str, config: Dict[str, Any]):
        """Initialize adapter."""
        self.source_id = source_id
        self.config = config
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """Fetch data from source."""
        raise NotImplementedError("SourceAdapter.fetch_data() not implemented")
    
    def normalize(self, raw_data: Any) -> List[Dict[str, Any]]:
        """Normalize raw data to standard format."""
        raise NotImplementedError("SourceAdapter.normalize() not implemented")
    
    def health(self) -> Dict[str, Any]:
        """Check source health."""
        raise NotImplementedError("SourceAdapter.health() not implemented")


# ============================================================================
# SOURCE REGISTRY
# ============================================================================

class SourceRegistry:
    """
    Registry for data sources.
    
    Manages:
    - Source registration
    - Status tracking
    - Health monitoring
    - Adapter management
    """
    
    def __init__(self):
        """Initialize source registry."""
        self.sources: Dict[str, SourceContract] = {}
        self.adapters: Dict[str, SourceAdapter] = {}
    
    def register(self, source: SourceContract, adapter: Optional[SourceAdapter] = None) -> None:
        """Register a new source."""
        if source.id in self.sources:
            raise ValueError(f"Source {source.id} already registered")
        self.sources[source.id] = source
        if adapter:
            self.adapters[source.id] = adapter
    
    def get(self, source_id: str) -> Optional[SourceContract]:
        """Get source by ID."""
        return self.sources.get(source_id)
    
    def update_status(self, source_id: str, status: SourceStatus) -> None:
        """Update source status."""
        if source_id not in self.sources:
            raise ValueError(f"Source {source_id} not found")
        self.sources[source_id].status = status
    
    def list_sources(self, status: Optional[SourceStatus] = None) -> List[SourceContract]:
        """List sources, optionally filtered by status."""
        if status is None:
            return list(self.sources.values())
        return [s for s in self.sources.values() if s.status == status]
    
    def get_adapter(self, source_id: str) -> Optional[SourceAdapter]:
        """Get adapter for source."""
        return self.adapters.get(source_id)
