"""
SAE Core Planning - Planning contracts and interfaces.

This module defines the planning system contracts for mission, orbital,
sensor, acquisition, and scheduler planning.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field
from ..common.enums import RiskLevel, generate_id, utc_now


# ============================================================================
# MISSION PLAN
# ============================================================================

@dataclass
class MissionPlan:
    """Plan for mission execution."""
    id: str
    mission_id: str
    steps: List[Dict[str, Any]]  # Ordered execution steps
    required_sources: List[str]
    required_models: List[str]
    estimated_duration: int  # seconds
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MissionPlanner:
    """
    Converts authorized requests into MissionPlans.
    
    Universal planner supporting:
    - Fire analysis
    - Flood assessment
    - Drought monitoring
    - Agriculture
    - Infrastructure
    - Energy
    - Environment
    - Civil protection
    - Territorial change
    """
    
    def plan(self, mission_id: str, objective: str, context: Dict[str, Any]) -> MissionPlan:
        """Generate mission plan."""
        raise NotImplementedError("MissionPlanner.plan() not implemented")


# ============================================================================
# ORBITAL PLANNER
# ============================================================================

@dataclass
class OrbitalState:
    """Satellite orbital state."""
    satellite_id: str
    tle: Optional[List[str]] = None  # Two-line element set
    position: Optional[Dict[str, float]] = None  # ECI coordinates
    velocity: Optional[Dict[str, float]] = None  # ECI velocity
    timestamp: datetime = field(default_factory=utc_now)


@dataclass
class AcquisitionPlan:
    """Plan for data acquisition."""
    id: str
    mission_id: str
    satellite: str
    sensor: str
    start_time: datetime
    end_time: datetime
    ground_track: List[Dict[str, float]] = field(default_factory=list)
    footprint: Optional[Dict[str, Any]] = None  # GeoJSON
    incidence_angle: Optional[float] = None
    expected_coverage: Optional[float] = None  # percentage
    priority: int = 5
    confidence: Optional[float] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    status: str = "planned"  # "planned", "confirmed", "executed", "failed"
    metadata: Dict[str, Any] = field(default_factory=dict)


class OrbitalPlanner:
    """
    Plans satellite acquisitions.
    
    Responsibilities:
    - Orbit propagation (SGP4 when TLE available)
    - Ground track prediction
    - Pass prediction
    - Visibility analysis
    - Sensor footprint calculation
    - Swath planning
    - Acquisition window identification
    - Sun geometry analysis
    - Incidence geometry analysis
    - Revisit analysis
    - Tasking optimization
    """
    
    def predict_passes(
        self,
        satellite_id: str,
        aoi: Dict[str, Any],
        time_window: Dict[str, datetime],
        constraints: Dict[str, Any]
    ) -> List[AcquisitionPlan]:
        """Predict satellite passes over AOI."""
        raise NotImplementedError("OrbitalPlanner.predict_passes() not implemented")
    
    def optimize_acquisition(self, candidates: List[AcquisitionPlan]) -> List[AcquisitionPlan]:
        """Optimize acquisition schedule."""
        raise NotImplementedError("OrbitalPlanner.optimize_acquisition() not implemented")


# ============================================================================
# SENSOR PLANNER
# ============================================================================

@dataclass
class SensorDefinition:
    """Sensor definition and capabilities."""
    id: str
    platform_id: str
    sensor_type: str  # "sar", "lidar", "optical", etc.
    modality: str
    swath: Optional[float] = None  # km
    resolution: Optional[Dict[str, float]] = None  # {"spatial": 10, "spectral": 0.01}
    incidence_constraints: Optional[Dict[str, float]] = None  # {"min": 20, "max": 50}
    operational_constraints: Dict[str, Any] = field(default_factory=dict)
    energy_cost: float = 1.0  # Relative energy cost
    storage_cost: float = 1.0  # Relative storage cost
    metadata: Dict[str, Any] = field(default_factory=dict)


class SensorPlanner:
    """
    Plans sensor operations.
    
    Supports:
    - SAR (polarization, frequency band, incidence geometry)
    - LiDAR (footprint, point density, sampling geometry)
    - Optical (spectral bands, resolution)
    - Future sensors
    """
    
    def plan_sensor_operation(
        self,
        sensor_id: str,
        aoi: Dict[str, Any],
        time_window: Dict[str, datetime],
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Plan sensor operation."""
        raise NotImplementedError("SensorPlanner.plan_sensor_operation() not implemented")


# ============================================================================
# ACQUISITION PLANNER
# ============================================================================

class AcquisitionPlanner:
    """
    Combines orbit, sensor, AOI, mission, and constraints.
    
    Generates candidate acquisition windows.
    Does NOT automatically order real acquisitions.
    """
    
    def __init__(
        self,
        orbital_planner: OrbitalPlanner,
        sensor_planner: SensorPlanner
    ):
        """Initialize with orbital and sensor planners."""
        self.orbital_planner = orbital_planner
        self.sensor_planner = sensor_planner
    
    def generate_candidates(
        self,
        mission_id: str,
        satellite_id: str,
        sensor_id: str,
        aoi: Dict[str, Any],
        time_window: Dict[str, datetime],
        constraints: Dict[str, Any]
    ) -> List[AcquisitionPlan]:
        """Generate acquisition candidates."""
        # Predict passes
        passes = self.orbital_planner.predict_passes(
            satellite_id, aoi, time_window, constraints
        )
        
        # Plan sensor operations
        candidates = []
        for pass_plan in passes:
            sensor_op = self.sensor_planner.plan_sensor_operation(
                sensor_id, aoi, 
                {"start": pass_plan.start_time, "end": pass_plan.end_time},
                constraints
            )
            
            # Combine into acquisition plan
            candidate = AcquisitionPlan(
                id=generate_id(),
                mission_id=mission_id,
                satellite=satellite_id,
                sensor=sensor_id,
                start_time=pass_plan.start_time,
                end_time=pass_plan.end_time,
                ground_track=pass_plan.ground_track,
                footprint=sensor_op.get("footprint"),
                incidence_angle=sensor_op.get("incidence_angle"),
                expected_coverage=sensor_op.get("coverage"),
                metadata={**pass_plan.metadata, **sensor_op}
            )
            candidates.append(candidate)
        
        return candidates


# ============================================================================
# SCHEDULER
# ============================================================================

@dataclass
class ScheduleItem:
    """Scheduled task."""
    id: str
    mission_id: str
    task_type: str  # "acquisition", "inference", "export", etc.
    start_time: datetime
    end_time: datetime
    priority: int
    resources: Dict[str, Any] = field(default_factory=dict)
    status: str = "scheduled"  # "scheduled", "running", "completed", "failed"
    metadata: Dict[str, Any] = field(default_factory=dict)


class Scheduler:
    """
    Resolves scheduling conflicts and priorities.
    
    Handles:
    - Priority resolution
    - Time window constraints
    - Sensor availability
    - Energy constraints
    - Storage constraints
    - Mission dependencies
    """
    
    def schedule(self, tasks: List[ScheduleItem]) -> List[ScheduleItem]:
        """Schedule tasks respecting constraints."""
        # Simple priority-based scheduling
        sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=False)
        
        # Check for conflicts
        scheduled = []
        for task in sorted_tasks:
            # Check resource conflicts
            conflict = False
            for existing in scheduled:
                if self._has_conflict(task, existing):
                    conflict = True
                    break
            
            if not conflict:
                scheduled.append(task)
        
        return scheduled
    
    def _has_conflict(self, task1: ScheduleItem, task2: ScheduleItem) -> bool:
        """Check if two tasks have resource conflicts."""
        # Time overlap
        if task1.end_time <= task2.start_time or task1.start_time >= task2.end_time:
            return False
        
        # Resource overlap
        for resource in task1.resources:
            if resource in task2.resources:
                return True
        
        return False
