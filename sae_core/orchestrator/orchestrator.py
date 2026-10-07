"""
SAE Intelligence Orchestrator - Base implementation.

This module implements the base SAE Intelligence Orchestrator that coordinates
all components of the SAE Core system.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field

from ..common.enums import (
    MissionStatus,
    ExecutionNodeStatus,
    PolicyDecision,
    EventType,
    RiskLevel,
    generate_id,
    utc_now,
    SAEError,
    PolicyDeniedError,
    ApprovalRequiredError,
)
from .contracts import (
    Mission,
    AreaOfInterest,
    TimeWindow,
    ExecutionGraph,
    ExecutionNode,
    MissionContext,
    Decision,
)
from ..ai.contracts import ModelRegistry, ModelRouter, ModelSelectionCriteria
from ..memory.contracts import WorkingMemory, MissionMemory
from ..security.contracts import PolicyEngine, PolicyContext, ApprovalEngine, AuditEngine
from ..events.contracts import EventBus, Event
from ..sources.contracts import SourceRegistry
from ..execution.contracts import ExecutionEngine


# ============================================================================
# SAE INTELLIGENCE ORCHESTRATOR
# ============================================================================

class SAEIntelligenceOrchestrator:
    """
    SAE Intelligence Orchestrator - Central coordinator.
    
    Responsibilities:
    - Interpret structured requests
    - Create context
    - Create/resolve missions
    - Consult memory
    - Resolve sources
    - Select models
    - Request planning
    - Build execution graph
    - Evaluate policy
    - Coordinate execution
    - Manage errors
    - Capture evidence
    - Generate explainable results
    
    Does NOT:
    - Skip permissions
    - Invent sources
    - Invent results
    - Execute sensitive operations without authorization
    - Mark evidence as verified arbitrarily
    """
    
    def __init__(
        self,
        model_registry: ModelRegistry,
        source_registry: SourceRegistry,
        policy_engine: PolicyEngine,
        approval_engine: ApprovalEngine,
        audit_engine: AuditEngine,
        event_bus: EventBus,
        execution_engine: ExecutionEngine
    ):
        """Initialize orchestrator with dependencies."""
        self.model_registry = model_registry
        self.source_registry = source_registry
        self.policy_engine = policy_engine
        self.approval_engine = approval_engine
        self.audit_engine = audit_engine
        self.event_bus = event_bus
        self.execution_engine = execution_engine
        
        # Memory
        self.working_memories: Dict[str, WorkingMemory] = {}
        self.mission_memories: Dict[str, MissionMemory] = {}
        
        # Missions
        self.missions: Dict[str, Mission] = {}
        self.execution_graphs: Dict[str, ExecutionGraph] = {}
    
    # ========================================================================
    # MISSION MANAGEMENT
    # ========================================================================
    
    def create_mission(
        self,
        name: str,
        objective: str,
        description: str,
        area_of_interest: AreaOfInterest,
        time_window: TimeWindow,
        priority: int,
        requested_products: List[str],
        required_sources: List[str],
        required_models: List[str],
        created_by: str,
        risk_level: RiskLevel = RiskLevel.LOW,
        approval_policy: str = "standard"
    ) -> Mission:
        """Create a new mission."""
        mission = Mission(
            id=generate_id(),
            name=name,
            objective=objective,
            description=description,
            area_of_interest=area_of_interest,
            time_window=time_window,
            priority=priority,
            requested_products=requested_products,
            required_sources=required_sources,
            required_models=required_models,
            risk_level=risk_level,
            approval_policy=approval_policy,
            created_by=created_by,
            status=MissionStatus.CREATED
        )
        
        self.missions[mission.id] = mission
        
        # Initialize working memory
        self.working_memories[mission.id] = WorkingMemory(mission_id=mission.id)
        
        # Initialize mission memory
        self.mission_memories[mission.id] = MissionMemory(mission_id=mission.id)
        
        # Audit
        self.audit_engine.record(
            actor=created_by,
            action="MISSION_CREATED",
            resource="mission",
            resource_id=mission.id,
            mission_id=mission.id
        )
        
        # Event
        self.event_bus.create_event(
            event_type=EventType.MISSION_CREATED,
            producer="orchestrator",
            payload={"mission_id": mission.id, "name": name},
            mission_id=mission.id
        )
        
        return mission
    
    # ========================================================================
    # EXECUTION
    # ========================================================================
    
    def execute_mission(self, mission_id: str, actor: str) -> Dict[str, Any]:
        """
        Execute a mission.
        
        Flow:
        1. Validate mission exists and is ready
        2. Build execution graph (if not exists)
        3. Evaluate policy
        4. Execute nodes in dependency order
        5. Capture evidence
        6. Record audit events
        7. Return results
        """
        if mission_id not in self.missions:
            raise ValueError(f"Mission {mission_id} not found")
        
        mission = self.missions[mission_id]
        
        # Validate state
        if mission.status not in [MissionStatus.READY, MissionStatus.RUNNING]:
            raise ValueError(f"Mission {mission_id} is not ready for execution (status: {mission.status})")
        
        # Transition to running
        mission.transition_to(MissionStatus.RUNNING)
        
        # Get or create execution graph
        if mission_id not in self.execution_graphs:
            # In real implementation, would build graph from mission plan
            self.execution_graphs[mission_id] = ExecutionGraph(
                id=generate_id(),
                mission_id=mission_id
            )
        
        graph = self.execution_graphs[mission_id]
        
        # Execute nodes
        results = {}
        max_iterations = 100  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            ready_nodes = graph.get_ready_nodes()
            
            if not ready_nodes:
                break
            
            for node in ready_nodes:
                # Check policy
                policy_context = PolicyContext(
                    actor=self._get_user(actor),
                    action="execute",
                    resource="execution_node",
                    resource_id=node.id,
                    mission_id=mission_id,
                    risk_level=node.risk_level
                )
                
                policy_result = self.policy_engine.evaluate(policy_context)
                
                if policy_result.decision == PolicyDecision.DENY:
                    node.status = ExecutionNodeStatus.FAILED
                    self.audit_engine.record(
                        actor=actor,
                        action="EXECUTION_DENIED",
                        resource="execution_node",
                        resource_id=node.id,
                        mission_id=mission_id,
                        status="failure",
                        metadata={"reason": policy_result.reason}
                    )
                    continue
                
                if policy_result.decision == PolicyDecision.REQUIRE_APPROVAL:
                    node.status = ExecutionNodeStatus.WAITING_FOR_APPROVAL
                    # In real implementation, would create approval request
                    continue
                
                # Execute node
                node.status = ExecutionNodeStatus.RUNNING
                
                try:
                    # In real implementation, would execute actual tool
                    result = self.execution_engine.execute_node(
                        node_id=node.id,
                        tool_id=node.type,
                        inputs=node.inputs,
                        context={"mission_id": mission_id}
                    )
                    
                    node.status = result.status
                    node.outputs = result.outputs
                    results[node.id] = result
                    
                    # Audit
                    self.audit_engine.record(
                        actor=actor,
                        action="EXECUTION_COMPLETED",
                        resource="execution_node",
                        resource_id=node.id,
                        mission_id=mission_id,
                        status="success" if result.status == ExecutionNodeStatus.SUCCEEDED else "failure"
                    )
                    
                except Exception as e:
                    node.status = ExecutionNodeStatus.FAILED
                    self.audit_engine.record(
                        actor=actor,
                        action="EXECUTION_FAILED",
                        resource="execution_node",
                        resource_id=node.id,
                        mission_id=mission_id,
                        status="failure",
                        metadata={"error": str(e)}
                    )
            
            iteration += 1
        
        # Transition to completed
        mission.transition_to(MissionStatus.COMPLETED)
        
        # Event
        self.event_bus.create_event(
            event_type=EventType.MISSION_COMPLETED,
            producer="orchestrator",
            payload={"mission_id": mission_id, "results": len(results)},
            mission_id=mission_id
        )
        
        return results
    
    # ========================================================================
    # HELPERS
    # ========================================================================
    
    def _get_user(self, user_id: str):
        """Get user (placeholder)."""
        from ..security.contracts import User
        from ..common.enums import UserRole
        return User(
            id=user_id,
            username=user_id,
            email=f"{user_id}@example.com",
            roles=[UserRole.OPERATOR]
        )
