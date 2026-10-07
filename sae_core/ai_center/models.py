"""
SAE AI Command & Training Center - Core Models

Defines all contracts, enums, and data structures for the AI center.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field


# ============================================================================
# COMMAND & INTENT MODELS
# ============================================================================

class AIIntent(str, Enum):
    """AI command intents."""
    # Exploration & Analysis
    EXPLORE_AREA = "EXPLORE_AREA"
    ANALYZE_CHANGE = "ANALYZE_CHANGE"
    ASSESS_RISK = "ASSESS_RISK"
    SEARCH_EVIDENCE = "SEARCH_EVIDENCE"
    COMPARE_DATA = "COMPARE_DATA"
    
    # Inference & Prediction
    RUN_INFERENCE = "RUN_INFERENCE"
    PREDICT_EVENT = "PREDICT_EVENT"
    
    # Planning
    PLAN_ACQUISITION = "PLAN_ACQUISITION"
    CREATE_MISSION = "CREATE_MISSION"
    
    # Model Management
    TRAIN_MODEL = "TRAIN_MODEL"
    FINE_TUNE_MODEL = "FINE_TUNE_MODEL"
    EVALUATE_MODEL = "EVALUATE_MODEL"
    COMPARE_MODELS = "COMPARE_MODELS"
    DEPLOY_MODEL = "DEPLOY_MODEL"
    DISABLE_MODEL = "DISABLE_MODEL"
    
    # Promotion
    CREATE_CAMPAIGN = "CREATE_CAMPAIGN"
    OPTIMIZE_PROMOTION = "OPTIMIZE_PROMOTION"
    
    # Output
    GENERATE_REPORT = "GENERATE_REPORT"
    EXPORT_RESULT = "EXPORT_RESULT"
    
    # Unknown
    UNKNOWN = "UNKNOWN"


class AICommandStatus(str, Enum):
    """AI command lifecycle states."""
    RECEIVED = "RECEIVED"
    PARSED = "PARSED"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class AICommand:
    """Structured AI command."""
    id: str
    actor: str
    raw_command: str
    intent: AIIntent
    mission_id: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    requested_capabilities: List[str] = field(default_factory=list)
    risk_level: str = "LOW"
    required_permissions: List[str] = field(default_factory=list)
    status: AICommandStatus = AICommandStatus.RECEIVED
    created_at: datetime = field(default_factory=datetime.utcnow)
    correlation_id: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# MODEL CAPABILITIES & TYPES
# ============================================================================

class ModelCapability(str, Enum):
    """Normalized model capabilities."""
    # Text & Reasoning
    TEXT_GENERATION = "TEXT_GENERATION"
    REASONING = "REASONING"
    STRUCTURED_OUTPUT = "STRUCTURED_OUTPUT"
    CODE_GENERATION = "CODE_GENERATION"
    
    # Vision & Image
    VISION = "VISION"
    IMAGE_ANALYSIS = "IMAGE_ANALYSIS"
    
    # Embeddings & Search
    EMBEDDINGS = "EMBEDDINGS"
    RERANKING = "RERANKING"
    
    # Classification & Detection
    CLASSIFICATION = "CLASSIFICATION"
    ANOMALY_DETECTION = "ANOMALY_DETECTION"
    
    # Time Series & Forecasting
    TIME_SERIES = "TIME_SERIES"
    FORECASTING = "FORECASTING"
    
    # Geospatial & Remote Sensing
    GEOSPATIAL = "GEOSPATIAL"
    REMOTE_SENSING = "REMOTE_SENSING"
    SAR_ANALYSIS = "SAR_ANALYSIS"
    LIDAR_ANALYSIS = "LIDAR_ANALYSIS"
    MULTIMODAL_FUSION = "MULTIMODAL_FUSION"
    
    # Promotion
    PROMOTION_RANKING = "PROMOTION_RANKING"


class ModelStatus(str, Enum):
    """Model lifecycle states."""
    REGISTERED = "REGISTERED"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    VALIDATING = "VALIDATING"
    VALIDATED = "VALIDATED"
    TRAINING = "TRAINING"
    CANDIDATE = "CANDIDATE"
    READY = "READY"
    DEPLOYED = "DEPLOYED"
    DEGRADED = "DEGRADED"
    RETIRED = "RETIRED"
    DISABLED = "DISABLED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class ModelType(str, Enum):
    """Model types."""
    LLM = "LLM"
    VLM = "VLM"
    EMBEDDING = "EMBEDDING"
    RERANKER = "RERANKER"
    CLASSIFIER = "CLASSIFIER"
    DETECTOR = "DETECTOR"
    FOUNDATION = "FOUNDATION"
    SCIENTIFIC = "SCIENTIFIC"
    PREDICTIVE = "PREDICTIVE"


@dataclass
class AIModel:
    """AI model registration."""
    id: str
    name: str
    provider: str
    version: str
    model_type: ModelType
    capabilities: List[ModelCapability]
    modalities: List[str]  # ["text", "image", "sar", "lidar", etc.]
    context_window: Optional[int] = None
    input_contract: Dict[str, Any] = field(default_factory=dict)
    output_contract: Dict[str, Any] = field(default_factory=dict)
    status: ModelStatus = ModelStatus.REGISTERED
    device: str = "cpu"
    precision: str = "fp32"
    checkpoint: Optional[str] = None
    training_status: Optional[str] = None
    validation_status: Optional[str] = None
    deployment_status: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# DATASET & TRAINING MODELS
# ============================================================================

class DatasetStatus(str, Enum):
    """Dataset validation states."""
    REGISTERED = "REGISTERED"
    VALIDATING = "VALIDATING"
    VALID = "VALID"
    INVALID = "INVALID"
    BLOCKED = "BLOCKED"
    DISABLED = "DISABLED"


@dataclass
class Dataset:
    """Dataset registration."""
    id: str
    name: str
    version: str
    modality: str
    location: str
    format: str
    schema: Dict[str, Any] = field(default_factory=dict)
    size: Optional[int] = None
    split_strategy: Optional[Dict[str, float]] = None
    license: Optional[str] = None
    provenance: Dict[str, Any] = field(default_factory=dict)
    validation_status: DatasetStatus = DatasetStatus.REGISTERED
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TrainingStatus(str, Enum):
    """Training job states."""
    DRAFT = "DRAFT"
    VALIDATING = "VALIDATING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    EVALUATING = "EVALUATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    BLOCKED = "BLOCKED"


class TrainingType(str, Enum):
    """Training types."""
    PRETRAINING = "PRETRAINING"
    FINE_TUNING = "FINE_TUNING"
    SUPERVISED_FINE_TUNING = "SUPERVISED_FINE_TUNING"
    LINEAR_PROBE = "LINEAR_PROBE"
    ADAPTER_TUNING = "ADAPTER_TUNING"
    LORA = "LORA"
    DOMAIN_ADAPTATION = "DOMAIN_ADAPTATION"


@dataclass
class TrainingJob:
    """Training job definition."""
    id: str
    model_id: str
    base_model: str
    dataset_id: str
    training_type: TrainingType
    config: Dict[str, Any] = field(default_factory=dict)
    status: TrainingStatus = TrainingStatus.DRAFT
    device: str = "cpu"
    precision: str = "fp32"
    requested_by: str = ""
    approved_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    checkpoint: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    correlation_id: str = ""


@dataclass
class Checkpoint:
    """Model checkpoint."""
    id: str
    model_id: str
    training_job_id: Optional[str] = None
    epoch: int = 0
    step: int = 0
    metrics: Dict[str, Any] = field(default_factory=dict)
    path: str = ""
    hash: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EvaluationRun:
    """Model evaluation run."""
    id: str
    model_id: str
    checkpoint: Optional[str] = None
    dataset_id: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    status: str = "PENDING"
    created_at: datetime = field(default_factory=datetime.utcnow)
    results: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)


@dataclass
class Experiment:
    """Experiment tracking."""
    id: str
    name: str
    run_id: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    dataset_id: Optional[str] = None
    model_id: Optional[str] = None
    checkpoint_id: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    status: str = "RUNNING"
    created_at: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# MODEL SELECTION & ROUTING
# ============================================================================

@dataclass
class AIRequest:
    """AI inference request."""
    id: str
    mission_id: Optional[str] = None
    intent: Optional[AIIntent] = None
    required_capabilities: List[ModelCapability] = field(default_factory=list)
    modalities: List[str] = field(default_factory=list)
    risk_level: str = "LOW"
    privacy_requirements: Dict[str, Any] = field(default_factory=dict)
    latency_requirement: Optional[float] = None
    cost_constraint: Optional[float] = None
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelSelection:
    """Model selection result."""
    selected_model: AIModel
    alternatives: List[AIModel] = field(default_factory=list)
    selection_reason: str = ""
    capability_match: Dict[str, Any] = field(default_factory=dict)
    policy_result: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# PROVIDER & ADAPTER MODELS
# ============================================================================

@dataclass
class ProviderConfig:
    """Provider configuration."""
    id: str
    name: str
    type: str  # "local", "remote", "api"
    endpoint: Optional[str] = None
    auth_type: Optional[str] = None  # "api_key", "oauth", "none"
    capabilities: List[ModelCapability] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
