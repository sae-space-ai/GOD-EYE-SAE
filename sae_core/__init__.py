"""
SAE Intelligence Core

Central intelligence system for GOD EYE SAE geospatial intelligence platform.

This package provides:
- SAE Intelligence Orchestrator
- AI Engine (Model Registry, Inference, Foundation Model Adapter)
- Memory Engine (Working, Mission, Spatial, Temporal, Semantic, Evidence)
- Planning Engine (Mission, Orbital, Sensor, Acquisition, Scheduler)
- Prediction Engine (Change, Forecasting, Risk, Anomaly)
- Evidence Engine (Capture, Provenance, Integrity)
- Security Engine (Identity, Authorization, Policy, Approvals, Audit)
- Event Bus (Asynchronous communication, correlation tracking)
- Source Registry (Data source management)
- Execution Engine (Tool execution, permissions)

Phase 4A: Contracts, schemas, interfaces, base orchestrator
"""

__version__ = "0.1.0"

from .common import (
    MissionStatus,
    ExecutionNodeStatus,
    SourceStatus,
    ModelStatus,
    EpistemicType,
    RiskLevel,
    DataClassification,
    ApprovalStatus,
    PolicyDecision,
    UserRole,
    IntentType,
    JobStatus,
    ToolType,
    EventType,
    SAEError,
    ValidationError,
    AuthorizationError,
    PolicyDeniedError,
    ApprovalRequiredError,
    SourceUnavailableError,
    ModelUnavailableError,
    MissionStateError,
    ExecutionError,
    EvidenceError,
    generate_id,
    utc_now,
)

from .orchestrator import (
    SAEIntelligenceOrchestrator,
    Mission,
    AreaOfInterest,
    TimeWindow,
    ExecutionGraph,
    ExecutionNode,
    MissionContext,
)

from .ai import (
    ModelContract,
    ModelRegistry,
    ModelRouter,
    InferenceRequest,
    InferenceResult,
    FoundationModelAdapter,
)

from .memory import (
    WorkingMemory,
    MissionMemory,
    SpatialMemory,
    TemporalMemory,
    SemanticMemory,
    EvidenceMemory,
)

from .planning import (
    MissionPlan,
    MissionPlanner,
    OrbitalPlanner,
    SensorPlanner,
    AcquisitionPlanner,
    Scheduler,
)

from .prediction import (
    PredictionResult,
    PredictionEngine,
)

from .evidence import (
    Evidence,
    EvidenceCapture,
    EvidenceVerification,
    Provenance,
)

from .security import (
    User,
    Role,
    Permission,
    PolicyEngine,
    ApprovalEngine,
    AuditEngine,
)

from .events import (
    Event,
    EventBus,
    CorrelationTracker,
)

from .sources import (
    SourceContract,
    SourceRegistry,
)

from .execution import (
    ToolContract,
    ExecutionEngine,
    ToolRegistry,
)

# Promotion Engine
from .promotion import (
    Campaign,
    Promotion,
    PromotionDecision,
    PromotionService,
    promotion_router,
)

# AI Command & Training Center
from .ai_center import (
    AICommand,
    AICommandStatus,
    AIIntent,
    ModelCapability,
    AIModel,
    ModelStatus,
    TrainingJob,
    TrainingStatus,
    Dataset,
    DatasetStatus,
    Checkpoint,
    EvaluationRun,
    Experiment,
    CommandCenter,
    ModelRegistry,
    ModelRouter,
    TrainingCenter,
    InferenceCenter,
)

__all__ = [
    # Version
    "__version__",
    
    # Common
    "MissionStatus",
    "ExecutionNodeStatus",
    "SourceStatus",
    "ModelStatus",
    "EpistemicType",
    "RiskLevel",
    "DataClassification",
    "ApprovalStatus",
    "PolicyDecision",
    "UserRole",
    "IntentType",
    "JobStatus",
    "ToolType",
    "EventType",
    "SAEError",
    "ValidationError",
    "AuthorizationError",
    "PolicyDeniedError",
    "ApprovalRequiredError",
    "SourceUnavailableError",
    "ModelUnavailableError",
    "MissionStateError",
    "ExecutionError",
    "EvidenceError",
    "generate_id",
    "utc_now",
    
    # Orchestrator
    "SAEIntelligenceOrchestrator",
    "Mission",
    "AreaOfInterest",
    "TimeWindow",
    "ExecutionGraph",
    "ExecutionNode",
    "MissionContext",
    
    # AI
    "ModelContract",
    "ModelRegistry",
    "ModelRouter",
    "InferenceRequest",
    "InferenceResult",
    "FoundationModelAdapter",
    
    # Memory
    "WorkingMemory",
    "MissionMemory",
    "SpatialMemory",
    "TemporalMemory",
    "SemanticMemory",
    "EvidenceMemory",
    
    # Planning
    "MissionPlan",
    "MissionPlanner",
    "OrbitalPlanner",
    "SensorPlanner",
    "AcquisitionPlanner",
    "Scheduler",
    
    # Prediction
    "PredictionResult",
    "PredictionEngine",
    
    # Evidence
    "Evidence",
    "EvidenceCapture",
    "EvidenceVerification",
    "Provenance",
    
    # Security
    "User",
    "Role",
    "Permission",
    "PolicyEngine",
    "ApprovalEngine",
    "AuditEngine",
    
    # Events
    "Event",
    "EventBus",
    "CorrelationTracker",
    
    # Sources
    "SourceContract",
    "SourceRegistry",
    
    # Execution
    "ToolContract",
    "ExecutionEngine",
    "ToolRegistry",
    
    # Promotion
    "Campaign",
    "Promotion",
    "PromotionDecision",
    "PromotionService",
    "promotion_router",
    
    # AI Center
    "AICommand",
    "AICommandStatus",
    "AIIntent",
    "ModelCapability",
    "AIModel",
    "ModelStatus",
    "TrainingJob",
    "TrainingStatus",
    "Dataset",
    "DatasetStatus",
    "Checkpoint",
    "EvaluationRun",
    "Experiment",
    "CommandCenter",
    "ModelRegistry",
    "ModelRouter",
    "TrainingCenter",
    "InferenceCenter",
]
