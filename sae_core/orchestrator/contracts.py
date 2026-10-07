"""
SAE Core Orchestrator - Mission and Execution Graph contracts.

This module defines the core mission and execution graph schemas
used by the SAE Intelligence Orchestrator.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field
from ..common.enums import (
    MissionStatus,
    ExecutionNodeStatus,
    RiskLevel,
    generate_id,
    utc_now,
)


# ============================================================================
# AREA OF INTEREST
# ============================================================================

@dataclass
class AreaOfInterest:
    """Geographic area of interest for a mission."""
    type: str  # "point", "bbox", "polygon"
    coordinates: Any  # Point: [lng, lat], BBox: [minx, miny, maxx, maxy], Polygon: [[[x,y],...]]
    crs: str = "EPSG:4326"  # Coordinate Reference System
    
    def validate(self) -> None:
        """Validate AOI structure."""
        if self.type == "point":
            if not isinstance(self.coordinates, list) or len(self.coordinates) != 2:
                raise ValueError("Point must have [longitude, latitude]")
        elif self.type == "bbox":
            if not isinstance(self.coordinates, list) or len(self.coordinates) != 4:
                raise ValueError("BBox must have [minx, miny, maxx, maxy]")
        elif self.type == "polygon":
            if not isinstance(self.coordinates, list):
                raise ValueError("Polygon must be a list of coordinate rings")
        else:
            raise ValueError(f"Unknown AOI type: {self.type}")


# ============================================================================
# TIME WINDOW
# ============================================================================

@dataclass
class TimeWindow:
    """Temporal window for a mission."""
    start: datetime
    end: datetime
    
    def validate(self) -> None:
        """Validate time window."""
        if self.end <= self.start:
            raise ValueError("End time must be after start time")


# ============================================================================
# MISSION
# ============================================================================

@dataclass
class Mission:
    """Mission definition and state."""
    id: str
    name: str
    objective: str
    description: str
    area_of_interest: AreaOfInterest
    time_window: TimeWindow
    priority: int  # 1 (highest) to 10 (lowest)
    requested_products: List[str]
    required_sources: List[str]
    required_models: List[str]
    constraints: Dict[str, Any] = field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.LOW
    approval_policy: str = "standard"
    status: MissionStatus = MissionStatus.CREATED
    created_by: str = ""
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def transition_to(self, new_status: MissionStatus) -> None:
        """Transition mission to new state with validation."""
        valid_transitions = {
            MissionStatus.CREATED: [MissionStatus.PLANNING, MissionStatus.CANCELLED],
            MissionStatus.PLANNING: [MissionStatus.WAITING_FOR_DATA, MissionStatus.READY, MissionStatus.CANCELLED],
            MissionStatus.WAITING_FOR_DATA: [MissionStatus.READY, MissionStatus.FAILED, MissionStatus.CANCELLED],
            MissionStatus.READY: [MissionStatus.RUNNING, MissionStatus.WAITING_FOR_APPROVAL, MissionStatus.CANCELLED],
            MissionStatus.RUNNING: [MissionStatus.COMPLETED, MissionStatus.FAILED, MissionStatus.WAITING_FOR_APPROVAL],
            MissionStatus.WAITING_FOR_APPROVAL: [MissionStatus.RUNNING, MissionStatus.CANCELLED],
            MissionStatus.COMPLETED: [],
            MissionStatus.FAILED: [],
            MissionStatus.CANCELLED: [],
        }
        
        if new_status not in valid_transitions.get(self.status, []):
            raise ValueError(f"Invalid transition from {self.status} to {new_status}")
        
        self.status = new_status
        self.updated_at = utc_now()


# ============================================================================
# EXECUTION NODE
# ============================================================================

@dataclass
class ExecutionNode:
    """Execution graph node."""
    id: str
    type: str  # "source_fetch", "inference", "prediction", "evidence_capture", etc.
    name: str
    dependencies: List[str] = field(default_factory=list)
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    status: ExecutionNodeStatus = ExecutionNodeStatus.PENDING
    risk_level: RiskLevel = RiskLevel.LOW
    requires_approval: bool = False
    retry_policy: Dict[str, Any] = field(default_factory=lambda: {"max_attempts": 3, "backoff": "exponential"})
    timeout: int = 300  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def can_execute(self, completed_nodes: set) -> bool:
        """Check if all dependencies are satisfied."""
        if self.status != ExecutionNodeStatus.READY:
            return False
        return all(dep in completed_nodes for dep in self.dependencies)


# ============================================================================
# EXECUTION GRAPH
# ============================================================================

@dataclass
class ExecutionGraph:
    """Directed acyclic graph of execution nodes."""
    id: str
    mission_id: str
    nodes: Dict[str, ExecutionNode] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    
    def add_node(self, node: ExecutionNode) -> None:
        """Add node to graph."""
        if node.id in self.nodes:
            raise ValueError(f"Node {node.id} already exists")
        self.nodes[node.id] = node
    
    def validate(self) -> None:
        """Validate graph structure (no cycles, dependencies exist)."""
        # Check all dependencies exist
        for node in self.nodes.values():
            for dep in node.dependencies:
                if dep not in self.nodes:
                    raise ValueError(f"Node {node.id} depends on non-existent node {dep}")
        
        # Check for cycles using topological sort
        visited = set()
        temp_mark = set()
        
        def has_cycle(node_id: str) -> bool:
            if node_id in temp_mark:
                return True
            if node_id in visited:
                return False
            
            temp_mark.add(node_id)
            node = self.nodes[node_id]
            
            for dep in node.dependencies:
                if has_cycle(dep):
                    return True
            
            temp_mark.remove(node_id)
            visited.add(node_id)
            return False
        
        for node_id in self.nodes:
            if has_cycle(node_id):
                raise ValueError("Execution graph contains cycles")
    
    def get_ready_nodes(self) -> List[ExecutionNode]:
        """Get nodes ready for execution."""
        completed = {
            node_id for node_id, node in self.nodes.items()
            if node.status in [ExecutionNodeStatus.SUCCEEDED, ExecutionNodeStatus.SKIPPED]
        }
        
        ready = []
        for node in self.nodes.values():
            if node.status == ExecutionNodeStatus.PENDING and node.can_execute(completed):
                ready.append(node)
        
        return ready


# ============================================================================
# DECISION
# ============================================================================

@dataclass
class Decision:
    """Decision record for audit trail."""
    id: str
    mission_id: str
    node_id: Optional[str]
    decision_type: str  # "policy", "approval", "routing", etc.
    decision: str
    reason: str
    made_by: str  # user_id or "system"
    made_at: datetime = field(default_factory=utc_now)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# MISSION CONTEXT
# ============================================================================

@dataclass
class MissionContext:
    """Runtime context for mission execution."""
    mission_id: str
    current_step: Optional[str] = None
    selected_entities: List[str] = field(default_factory=list)
    observations: List[Dict[str, Any]] = field(default_factory=list)
    intermediate_results: Dict[str, Any] = field(default_factory=dict)
    tool_results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    correlation_id: str = field(default_factory=generate_id)
    
    def add_observation(self, observation: Dict[str, Any]) -> None:
        """Add observation to context."""
        self.observations.append(observation)
    
    def set_result(self, key: str, value: Any) -> None:
        """Set intermediate result."""
        self.intermediate_results[key] = value
    
    def add_error(self, error: str) -> None:
        """Add error to context."""
        self.errors.append(error)
