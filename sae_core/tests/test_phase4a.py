"""
SAE Core Tests - Phase 4A validation.

Tests for:
- Mission state transitions
- Execution graph dependencies
- Policy ALLOW/DENY/REQUIRE_APPROVAL
- Approval transitions
- Permission checks
- Event serialization
- Correlation propagation
- Model registry
- Source registry
- Evidence hash
- Epistemic types
- Unauthorized execution rejection
"""

import pytest
from datetime import datetime, timedelta

from sae_core.common.enums import (
    MissionStatus,
    ExecutionNodeStatus,
    PolicyDecision,
    RiskLevel,
    UserRole,
    EventType,
    EpistemicType,
    ApprovalStatus,
)
from sae_core.orchestrator.contracts import (
    Mission,
    AreaOfInterest,
    TimeWindow,
    ExecutionGraph,
    ExecutionNode,
)
from sae_core.security.contracts import (
    User,
    Role,
    PolicyEngine,
    PolicyContext,
    Approval,
    AuditEngine,
)
from sae_core.events.contracts import Event, EventBus, CorrelationTracker
from sae_core.ai.contracts import ModelContract, ModelRegistry, ModelStatus
from sae_core.sources.contracts import SourceContract, SourceRegistry, SourceStatus
from sae_core.evidence.contracts import Evidence, EvidenceCapture, Provenance
from sae_core.prediction.contracts import PredictionResult


# ============================================================================
# MISSION STATE TRANSITIONS
# ============================================================================

class TestMissionStateTransitions:
    """Test mission state machine."""
    
    def test_valid_transition_created_to_planning(self):
        """Test valid transition from CREATED to PLANNING."""
        mission = Mission(
            id="test-mission",
            name="Test",
            objective="Test objective",
            description="Test description",
            area_of_interest=AreaOfInterest(type="point", coordinates=[0, 0]),
            time_window=TimeWindow(start=datetime.now(), end=datetime.now() + timedelta(hours=1)),
            priority=5,
            requested_products=["product1"],
            required_sources=["source1"],
            required_models=["model1"],
            status=MissionStatus.CREATED
        )
        
        mission.transition_to(MissionStatus.PLANNING)
        assert mission.status == MissionStatus.PLANNING
    
    def test_invalid_transition_created_to_running(self):
        """Test invalid transition from CREATED to RUNNING."""
        mission = Mission(
            id="test-mission",
            name="Test",
            objective="Test objective",
            description="Test description",
            area_of_interest=AreaOfInterest(type="point", coordinates=[0, 0]),
            time_window=TimeWindow(start=datetime.now(), end=datetime.now() + timedelta(hours=1)),
            priority=5,
            requested_products=["product1"],
            required_sources=["source1"],
            required_models=["model1"],
            status=MissionStatus.CREATED
        )
        
        with pytest.raises(ValueError, match="Invalid transition"):
            mission.transition_to(MissionStatus.RUNNING)
    
    def test_completed_is_terminal(self):
        """Test COMPLETED is terminal state."""
        mission = Mission(
            id="test-mission",
            name="Test",
            objective="Test objective",
            description="Test description",
            area_of_interest=AreaOfInterest(type="point", coordinates=[0, 0]),
            time_window=TimeWindow(start=datetime.now(), end=datetime.now() + timedelta(hours=1)),
            priority=5,
            requested_products=["product1"],
            required_sources=["source1"],
            required_models=["model1"],
            status=MissionStatus.COMPLETED
        )
        
        with pytest.raises(ValueError, match="Invalid transition"):
            mission.transition_to(MissionStatus.RUNNING)


# ============================================================================
# EXECUTION GRAPH DEPENDENCIES
# ============================================================================

class TestExecutionGraph:
    """Test execution graph dependencies."""
    
    def test_node_dependencies_satisfied(self):
        """Test node can execute when dependencies are satisfied."""
        node1 = ExecutionNode(id="node1", type="source_fetch", name="Fetch Source")
        node1.status = ExecutionNodeStatus.SUCCEEDED
        
        node2 = ExecutionNode(id="node2", type="inference", name="Run Model", dependencies=["node1"])
        node2.status = ExecutionNodeStatus.READY
        
        graph = ExecutionGraph(id="graph1", mission_id="mission1")
        graph.add_node(node1)
        graph.add_node(node2)
        
        ready = graph.get_ready_nodes()
        assert len(ready) == 1
        assert ready[0].id == "node2"
    
    def test_node_dependencies_not_satisfied(self):
        """Test node cannot execute when dependencies are not satisfied."""
        node1 = ExecutionNode(id="node1", type="source_fetch", name="Fetch Source")
        node1.status = ExecutionNodeStatus.PENDING
        
        node2 = ExecutionNode(id="node2", type="inference", name="Run Model", dependencies=["node1"])
        node2.status = ExecutionNodeStatus.READY
        
        graph = ExecutionGraph(id="graph1", mission_id="mission1")
        graph.add_node(node1)
        graph.add_node(node2)
        
        ready = graph.get_ready_nodes()
        assert len(ready) == 0
    
    def test_cycle_detection(self):
        """Test cycle detection in execution graph."""
        node1 = ExecutionNode(id="node1", type="source_fetch", name="Fetch", dependencies=["node2"])
        node2 = ExecutionNode(id="node2", type="inference", name="Infer", dependencies=["node1"])
        
        graph = ExecutionGraph(id="graph1", mission_id="mission1")
        graph.add_node(node1)
        graph.add_node(node2)
        
        with pytest.raises(ValueError, match="cycles"):
            graph.validate()


# ============================================================================
# POLICY ENGINE
# ============================================================================

class TestPolicyEngine:
    """Test policy engine decisions."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.roles = {
            "viewer": Role(id="viewer", name=UserRole.VIEWER, description="Viewer", permissions=["mission.read"]),
            "operator": Role(id="operator", name=UserRole.OPERATOR, description="Operator", permissions=["mission.read", "mission.execute"]),
        }
        self.policy_engine = PolicyEngine(self.roles)
    
    def test_policy_allow(self):
        """Test policy allows permitted action."""
        user = User(id="user1", username="operator", email="op@test.com", roles=[UserRole.OPERATOR])
        context = PolicyContext(actor=user, action="execute", resource="mission", risk_level=RiskLevel.LOW)
        
        result = self.policy_engine.evaluate(context)
        assert result.decision == PolicyDecision.ALLOW
    
    def test_policy_deny(self):
        """Test policy denies unauthorized action."""
        user = User(id="user1", username="viewer", email="view@test.com", roles=[UserRole.VIEWER])
        context = PolicyContext(actor=user, action="execute", resource="mission", risk_level=RiskLevel.LOW)
        
        result = self.policy_engine.evaluate(context)
        assert result.decision == PolicyDecision.DENY
    
    def test_policy_require_approval(self):
        """Test policy requires approval for high-risk actions."""
        user = User(id="user1", username="operator", email="op@test.com", roles=[UserRole.OPERATOR])
        context = PolicyContext(actor=user, action="execute", resource="mission", risk_level=RiskLevel.HIGH)
        
        result = self.policy_engine.evaluate(context)
        assert result.decision == PolicyDecision.REQUIRE_APPROVAL


# ============================================================================
# APPROVAL ENGINE
# ============================================================================

class TestApprovalEngine:
    """Test approval workflow."""
    
    def test_approval_transition_pending_to_approved(self):
        """Test approval can transition from PENDING to APPROVED."""
        approval = Approval(
            id="approval1",
            mission_id="mission1",
            execution_node_id="node1",
            requested_by="user1",
            requested_at=datetime.now()
        )
        
        approval.approve("reviewer1", "Approved for testing")
        assert approval.decision == ApprovalStatus.APPROVED
        assert approval.reviewed_by == "reviewer1"
    
    def test_approval_transition_pending_to_rejected(self):
        """Test approval can transition from PENDING to REJECTED."""
        approval = Approval(
            id="approval1",
            mission_id="mission1",
            execution_node_id="node1",
            requested_by="user1",
            requested_at=datetime.now()
        )
        
        approval.reject("reviewer1", "Rejected for testing")
        assert approval.decision == ApprovalStatus.REJECTED
        assert approval.reviewed_by == "reviewer1"
    
    def test_cannot_approve_already_approved(self):
        """Test cannot approve already approved request."""
        approval = Approval(
            id="approval1",
            mission_id="mission1",
            execution_node_id="node1",
            requested_by="user1",
            requested_at=datetime.now(),
            decision=ApprovalStatus.APPROVED
        )
        
        with pytest.raises(ValueError, match="Cannot approve"):
            approval.approve("reviewer1")


# ============================================================================
# EVENT BUS
# ============================================================================

class TestEventBus:
    """Test event bus and correlation."""
    
    def test_event_publish_subscribe(self):
        """Test event publish and subscribe."""
        bus = EventBus()
        received = []
        
        def handler(event):
            received.append(event)
        
        bus.subscribe(EventType.MISSION_CREATED, handler)
        
        event = bus.create_event(
            event_type=EventType.MISSION_CREATED,
            producer="test",
            payload={"mission_id": "mission1"}
        )
        
        assert len(received) == 1
        assert received[0].id == event.id
    
    def test_correlation_propagation(self):
        """Test correlation ID propagation."""
        tracker = CorrelationTracker()
        correlation_id = tracker.start_correlation()
        
        assert tracker.get_correlation_id() == correlation_id
        
        tracker.end_correlation()
        assert tracker.get_correlation_id() is None


# ============================================================================
# MODEL REGISTRY
# ============================================================================

class TestModelRegistry:
    """Test model registry."""
    
    def test_register_model(self):
        """Test model registration."""
        registry = ModelRegistry()
        model = ModelContract(
            id="model1",
            name="Test Model",
            version="1.0",
            model_type="foundation_model",
            modalities=["lidar", "sar"],
            input_contract={},
            output_contract={}
        )
        
        registry.register(model)
        assert registry.get("model1") is not None
    
    def test_cannot_register_duplicate(self):
        """Test cannot register duplicate model."""
        registry = ModelRegistry()
        model = ModelContract(
            id="model1",
            name="Test Model",
            version="1.0",
            model_type="foundation_model",
            modalities=["lidar", "sar"],
            input_contract={},
            output_contract={}
        )
        
        registry.register(model)
        
        with pytest.raises(ValueError, match="already registered"):
            registry.register(model)


# ============================================================================
# SOURCE REGISTRY
# ============================================================================

class TestSourceRegistry:
    """Test source registry."""
    
    def test_register_source(self):
        """Test source registration."""
        registry = SourceRegistry()
        source = SourceContract(
            id="source1",
            name="Test Source",
            category="test",
            provider="test"
        )
        
        registry.register(source)
        assert registry.get("source1") is not None
    
    def test_update_source_status(self):
        """Test source status update."""
        registry = SourceRegistry()
        source = SourceContract(
            id="source1",
            name="Test Source",
            category="test",
            provider="test"
        )
        
        registry.register(source)
        registry.update_status("source1", SourceStatus.INTEGRATED_VERIFIED)
        
        assert registry.get("source1").status == SourceStatus.INTEGRATED_VERIFIED


# ============================================================================
# EVIDENCE HASH
# ============================================================================

class TestEvidenceHash:
    """Test evidence integrity hash."""
    
    def test_evidence_hash_computation(self):
        """Test evidence hash is computed correctly."""
        evidence = Evidence(
            id="evidence1",
            mission_id="mission1",
            source_id="source1",
            entity_id="entity1",
            entity_type="earthquake",
            captured_at=datetime.now(),
            source_timestamp=datetime.now(),
            coordinates={"latitude": 0.0, "longitude": 0.0},
            snapshot='{"test": "data"}'
        )
        
        hash1 = evidence.compute_hash()
        assert len(hash1) == 64  # SHA-256 produces 64 hex chars
    
    def test_evidence_integrity_verification(self):
        """Test evidence integrity verification."""
        evidence = Evidence(
            id="evidence1",
            mission_id="mission1",
            source_id="source1",
            entity_id="entity1",
            entity_type="earthquake",
            captured_at=datetime.now(),
            source_timestamp=datetime.now(),
            coordinates={"latitude": 0.0, "longitude": 0.0},
            snapshot='{"test": "data"}'
        )
        
        evidence.hash = evidence.compute_hash()
        assert evidence.verify_integrity() is True
        
        # Modify evidence
        evidence.snapshot = '{"test": "modified"}'
        assert evidence.verify_integrity() is False


# ============================================================================
# EPISTEMIC TYPES
# ============================================================================

class TestEpistemicTypes:
    """Test epistemic type validation."""
    
    def test_prediction_cannot_be_observed(self):
        """Test prediction cannot be marked as OBSERVED."""
        prediction = PredictionResult(
            id="pred1",
            mission_id="mission1",
            prediction_type="risk",
            model_id="model1",
            model_version="1.0",
            generated_at=datetime.now(),
            valid_from=datetime.now(),
            valid_until=datetime.now() + timedelta(days=1),
            geometry={"type": "Point", "coordinates": [0, 0]},
            value=0.5,
            epistemic_type=EpistemicType.OBSERVED
        )
        
        with pytest.raises(ValueError, match="cannot be OBSERVED"):
            prediction.validate_epistemic_type()
    
    def test_prediction_can_be_predicted(self):
        """Test prediction can be marked as PREDICTED."""
        prediction = PredictionResult(
            id="pred1",
            mission_id="mission1",
            prediction_type="risk",
            model_id="model1",
            model_version="1.0",
            generated_at=datetime.now(),
            valid_from=datetime.now(),
            valid_until=datetime.now() + timedelta(days=1),
            geometry={"type": "Point", "coordinates": [0, 0]},
            value=0.5,
            epistemic_type=EpistemicType.PREDICTED
        )
        
        prediction.validate_epistemic_type()  # Should not raise


# ============================================================================
# UNAUTHORIZED EXECUTION REJECTION
# ============================================================================

class TestUnauthorizedExecution:
    """Test unauthorized execution is rejected."""
    
    def test_viewer_cannot_execute_mission(self):
        """Test VIEWER cannot execute mission."""
        roles = {
            "viewer": Role(id="viewer", name=UserRole.VIEWER, description="Viewer", permissions=["mission.read"]),
        }
        policy_engine = PolicyEngine(roles)
        
        user = User(id="user1", username="viewer", email="view@test.com", roles=[UserRole.VIEWER])
        context = PolicyContext(actor=user, action="execute", resource="mission")
        
        result = policy_engine.evaluate(context)
        assert result.decision == PolicyDecision.DENY


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
