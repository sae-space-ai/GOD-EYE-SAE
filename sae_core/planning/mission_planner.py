"""
SAE Core Planning - Deterministic Mission Planner.

This module implements a deterministic mission planner that converts
structured intents into execution graphs without requiring LLM.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from ..common.enums import (
    IntentType,
    ExecutionNodeStatus,
    RiskLevel,
    generate_id,
)
from ..orchestrator.contracts import (
    Mission,
    ExecutionGraph,
    ExecutionNode,
    AreaOfInterest,
    TimeWindow,
)
from ..sources.contracts import SourceRegistry
from ..ai.contracts import ModelRegistry


class DeterministicMissionPlanner:
    """
    Deterministic mission planner that generates execution graphs
    based on mission objectives and available resources.
    """
    
    def __init__(
        self,
        source_registry: SourceRegistry,
        model_registry: ModelRegistry
    ):
        """Initialize planner with registries."""
        self.source_registry = source_registry
        self.model_registry = model_registry
    
    def plan(
        self,
        mission: Mission,
        intent: IntentType
    ) -> ExecutionGraph:
        """
        Generate execution graph for a mission based on intent.
        
        Args:
            mission: Mission to plan
            intent: Type of intent (EXPLORE_AREA, ASSESS_RISK, etc.)
        
        Returns:
            ExecutionGraph with nodes and dependencies
        """
        graph = ExecutionGraph(
            id=generate_id(),
            mission_id=mission.id
        )
        
        # Generate nodes based on intent type
        if intent == IntentType.EXPLORE_AREA:
            nodes = self._plan_explore_area(mission)
        elif intent == IntentType.ASSESS_RISK:
            nodes = self._plan_assess_risk(mission)
        elif intent == IntentType.ANALYZE_CHANGE:
            nodes = self._plan_analyze_change(mission)
        elif intent == IntentType.SEARCH_EVIDENCE:
            nodes = self._plan_search_evidence(mission)
        else:
            # Default: basic exploration
            nodes = self._plan_explore_area(mission)
        
        # Add nodes to graph
        for node in nodes:
            graph.add_node(node)
        
        # Validate graph (check for cycles)
        graph.validate()
        
        return graph
    
    def _plan_explore_area(self, mission: Mission) -> List[ExecutionNode]:
        """Plan for EXPLORE_AREA intent."""
        nodes = []
        
        # Node 1: Resolve AOI
        node1 = ExecutionNode(
            id=generate_id(),
            type="resolve_aoi",
            name="Resolve Area of Interest",
            dependencies=[],
            inputs={"aoi": mission.area_of_interest},
            outputs={"resolved_aoi": None},
            status=ExecutionNodeStatus.PENDING,
            risk_level=RiskLevel.LOW
        )
        nodes.append(node1)
        
        # Node 2: Fetch source data
        node2 = ExecutionNode(
            id=generate_id(),
            type="fetch_sources",
            name="Fetch Source Data",
            dependencies=[node1.id],
            inputs={"sources": mission.required_sources, "aoi": mission.area_of_interest},
            outputs={"source_data": None},
            status=ExecutionNodeStatus.PENDING,
            risk_level=RiskLevel.LOW
        )
        nodes.append(node2)
        
        # Node 3: Process data
        node3 = ExecutionNode(
            id=generate_id(),
            type="process_data",
            name="Process Data",
            dependencies=[node2.id],
            inputs={"source_data": None},
            outputs={"processed_data": None},
            status=ExecutionNodeStatus.PENDING,
            risk_level=RiskLevel.LOW
        )
        nodes.append(node3)
        
        # Node 4: Capture evidence
        node4 = ExecutionNode(
            id=generate_id(),
            type="capture_evidence",
            name="Capture Evidence",
            dependencies=[node3.id],
            inputs={"processed_data": None},
            outputs={"evidence_ids": None},
            status=ExecutionNodeStatus.PENDING,
            risk_level=RiskLevel.LOW
        )
        nodes.append(node4)
        
        return nodes
    
    def _plan_assess_risk(self, mission: Mission) -> List[ExecutionNode]:
        """Plan for ASSESS_RISK intent."""
        nodes = []
        
        # Node 1: Resolve AOI
        node1 = ExecutionNode(
            id=generate_id(),
            type="resolve_aoi",
            name="Resolve Area of Interest",
            dependencies=[],
            inputs={"aoi": mission.area_of_interest},
            outputs={"resolved_aoi": None},
            status=ExecutionNodeStatus.PENDING,
            risk_level=RiskLevel.LOW
        )
        nodes.append(node1)
        
        # Node 2: Fetch historical data
        node2 = ExecutionNode(
            id=generate_id(),
            type="fetch_history",
            name="Fetch Historical Data",
            dependencies=[node1.id],
            inputs={"sources": mission.required_sources, "aoi": mission.area_of_interest},
            outputs={"historical_data": None},
            status=ExecutionNodeStatus.PENDING,
            risk_level=RiskLevel.LOW
        )
        nodes.append(node2)
        
        # Node 3: Fetch current data
        node3 = ExecutionNode(
            id=generate_id(),
            type="fetch_current",
            name="Fetch Current Data",
            dependencies=[node1.id],
            inputs={"sources": mission.required_sources, "aoi": mission.area_of_interest},
            outputs={"current_data": None},
            status=ExecutionNodeStatus.PENDING,
            risk_level=RiskLevel.LOW
        )
        nodes.append(node3)
        
        # Node 4: Run risk model
        node4 = ExecutionNode(
            id=generate_id(),
            type="run_inference",
            name="Run Risk Assessment Model",
            dependencies=[node2.id, node3.id],
            inputs={"historical_data": None, "current_data": None, "models": mission.required_models},
            outputs={"risk_assessment": None},
            status=ExecutionNodeStatus.PENDING,
            risk_level=RiskLevel.MEDIUM,
            requires_approval=True
        )
        nodes.append(node4)
        
        # Node 5: Capture evidence
        node5 = ExecutionNode(
            id=generate_id(),
            type="capture_evidence",
            name="Capture Evidence",
            dependencies=[node4.id],
            inputs={"risk_assessment": None},
            outputs={"evidence_ids": None},
            status=ExecutionNodeStatus.PENDING,
            risk_level=RiskLevel.LOW
        )
        nodes.append(node5)
        
        return nodes
    
    def _plan_analyze_change(self, mission: Mission) -> List[ExecutionNode]:
        """Plan for ANALYZE_CHANGE intent."""
        nodes = []
        
        # Node 1: Resolve AOI
        node1 = ExecutionNode(
            id=generate_id(),
            type="resolve_aoi",
            name="Resolve Area of Interest",
            dependencies=[],
            inputs={"aoi": mission.area_of_interest},
            outputs={"resolved_aoi": None},
            status=ExecutionNodeStatus.PENDING,
            risk_level=RiskLevel.LOW
        )
        nodes.append(node1)
        
        # Node 2: Fetch time series data
        node2 = ExecutionNode(
            id=generate_id(),
            type="fetch_timeseries",
            name="Fetch Time Series Data",
            dependencies=[node1.id],
            inputs={"sources": mission.required_sources, "aoi": mission.area_of_interest, "time_window": mission.time_window},
            outputs={"timeseries_data": None},
            status=ExecutionNodeStatus.PENDING,
            risk_level=RiskLevel.LOW
        )
        nodes.append(node2)
        
        # Node 3: Run change detection
        node3 = ExecutionNode(
            id=generate_id(),
            type="run_inference",
            name="Run Change Detection",
            dependencies=[node2.id],
            inputs={"timeseries_data": None, "models": mission.required_models},
            outputs={"change_analysis": None},
            status=ExecutionNodeStatus.PENDING,
            risk_level=RiskLevel.MEDIUM
        )
        nodes.append(node3)
        
        # Node 4: Capture evidence
        node4 = ExecutionNode(
            id=generate_id(),
            type="capture_evidence",
            name="Capture Evidence",
            dependencies=[node3.id],
            inputs={"change_analysis": None},
            outputs={"evidence_ids": None},
            status=ExecutionNodeStatus.PENDING,
            risk_level=RiskLevel.LOW
        )
        nodes.append(node4)
        
        return nodes
    
    def _plan_search_evidence(self, mission: Mission) -> List[ExecutionNode]:
        """Plan for SEARCH_EVIDENCE intent."""
        nodes = []
        
        # Node 1: Resolve AOI
        node1 = ExecutionNode(
            id=generate_id(),
            type="resolve_aoi",
            name="Resolve Area of Interest",
            dependencies=[],
            inputs={"aoi": mission.area_of_interest},
            outputs={"resolved_aoi": None},
            status=ExecutionNodeStatus.PENDING,
            risk_level=RiskLevel.LOW
        )
        nodes.append(node1)
        
        # Node 2: Search evidence database
        node2 = ExecutionNode(
            id=generate_id(),
            type="search_evidence",
            name="Search Evidence Database",
            dependencies=[node1.id],
            inputs={"aoi": mission.area_of_interest, "time_window": mission.time_window},
            outputs={"evidence_results": None},
            status=ExecutionNodeStatus.PENDING,
            risk_level=RiskLevel.LOW
        )
        nodes.append(node2)
        
        return nodes
    
    def check_source_availability(self, source_ids: List[str]) -> Dict[str, bool]:
        """Check availability of required sources."""
        availability = {}
        for source_id in source_ids:
            source = self.source_registry.get(source_id)
            if source:
                availability[source_id] = source.status in ["INTEGRATED_VERIFIED", "INTEGRATED_UNVERIFIED"]
            else:
                availability[source_id] = False
        return availability
    
    def check_model_availability(self, model_ids: List[str]) -> Dict[str, bool]:
        """Check availability of required models."""
        availability = {}
        for model_id in model_ids:
            model = self.model_registry.get(model_id)
            if model:
                availability[model_id] = model.status in ["READY", "DEGRADED"]
            else:
                availability[model_id] = False
        return availability
