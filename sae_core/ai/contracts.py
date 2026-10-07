"""
SAE Core AI Engine - Model and Inference contracts.

This module defines the AI model registry, inference contracts,
and foundation model adapter interfaces.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field
from ..common.enums import (
    ModelStatus,
    EpistemicType,
    generate_id,
    utc_now,
)


# ============================================================================
# MODEL CONTRACT
# ============================================================================

@dataclass
class ModelContract:
    """AI model definition and metadata."""
    id: str
    name: str
    version: str
    model_type: str  # "foundation_model", "classifier", "detector", etc.
    modalities: List[str]  # ["lidar", "sar", "optical", etc.]
    input_contract: Dict[str, Any]  # Input schema
    output_contract: Dict[str, Any]  # Output schema
    status: ModelStatus = ModelStatus.REGISTERED
    device: str = "cpu"  # "cpu", "cuda", "mps"
    precision: str = "fp32"  # "fp32", "fp16", "bf16"
    frozen: bool = False
    checkpoint: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate_status_for_inference(self) -> None:
        """Validate model is ready for inference."""
        if self.status not in [ModelStatus.READY, ModelStatus.DEGRADED]:
            raise ValueError(f"Model {self.id} is not ready for inference (status: {self.status})")


# ============================================================================
# INFERENCE REQUEST
# ============================================================================

@dataclass
class InferenceRequest:
    """Request for model inference."""
    id: str
    mission_id: str
    model_id: str
    inputs: Dict[str, Any]
    requested_outputs: List[str]
    device: str = "cpu"
    precision: str = "fp32"
    created_at: datetime = field(default_factory=utc_now)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# INFERENCE RESULT
# ============================================================================

@dataclass
class InferenceResult:
    """Result from model inference."""
    id: str
    request_id: str
    model_id: str
    model_version: str
    timestamp: datetime
    outputs: Dict[str, Any]
    confidence: Optional[float] = None  # Model confidence score
    uncertainty: Optional[float] = None  # Uncertainty estimate
    provenance: Dict[str, Any] = field(default_factory=dict)
    evidence_ids: List[str] = field(default_factory=list)
    status: str = "completed"  # "completed", "failed", "partial"
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# FOUNDATION MODEL ADAPTER INTERFACE
# ============================================================================

class FoundationModelAdapter:
    """
    Interface for foundation model adapters.
    
    This decouples SAE Core from the actual model runtime (PyTorch, remote service, etc.)
    """
    
    def __init__(self, model_id: str, config: Dict[str, Any]):
        """Initialize adapter."""
        self.model_id = model_id
        self.config = config
    
    def health(self) -> Dict[str, Any]:
        """Check model health."""
        raise NotImplementedError("Subclasses must implement health()")
    
    def metadata(self) -> ModelContract:
        """Get model metadata."""
        raise NotImplementedError("Subclasses must implement metadata()")
    
    def encode(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Encode inputs to latent representation."""
        raise NotImplementedError("Subclasses must implement encode()")
    
    def infer(self, inputs: Dict[str, Any]) -> InferenceResult:
        """Run inference on inputs."""
        raise NotImplementedError("Subclasses must implement infer()")


# ============================================================================
# MODEL ROUTER
# ============================================================================

@dataclass
class ModelSelectionCriteria:
    """Criteria for model selection."""
    mission_id: str
    requested_product: str
    available_modalities: List[str]
    device: str = "cpu"
    latency_requirement: Optional[float] = None  # seconds
    accuracy_requirement: Optional[float] = None  # 0.0 to 1.0
    permissions: List[str] = field(default_factory=list)


class ModelRouter:
    """
    Routes inference requests to appropriate models.
    
    Selects model based on:
    - Mission requirements
    - Available modalities
    - Model status
    - Device constraints
    - Performance requirements
    - User permissions
    """
    
    def __init__(self, registry: Dict[str, ModelContract]):
        """Initialize router with model registry."""
        self.registry = registry
    
    def select_model(self, criteria: ModelSelectionCriteria) -> Optional[ModelContract]:
        """Select best model for criteria."""
        candidates = []
        
        for model in self.registry.values():
            # Skip disabled/failed models
            if model.status in [ModelStatus.DISABLED, ModelStatus.FAILED]:
                continue
            
            # Check modality support
            if not any(mod in model.modalities for mod in criteria.available_modalities):
                continue
            
            # Check device compatibility
            if criteria.device not in ["cpu", "any"] and model.device != criteria.device:
                continue
            
            # Check permissions
            if f"model.infer.{model.id}" not in criteria.permissions and "model.infer.*" not in criteria.permissions:
                continue
            
            candidates.append(model)
        
        if not candidates:
            return None
        
        # Simple selection: prefer READY over DEGRADED, then by version
        candidates.sort(key=lambda m: (0 if m.status == ModelStatus.READY else 1, m.version), reverse=False)
        
        return candidates[0]


# ============================================================================
# UNCERTAINTY ENGINE
# ============================================================================

@dataclass
class UncertaintyEstimate:
    """Uncertainty estimate for a prediction or inference."""
    value: float  # 0.0 to 1.0
    type: str  # "aleatoric", "epistemic", "total"
    confidence_interval: Optional[tuple] = None  # (lower, upper)
    metadata: Dict[str, Any] = field(default_factory=dict)


class UncertaintyEngine:
    """
    Estimates uncertainty for model outputs.
    
    Supports:
    - Aleatoric uncertainty (data noise)
    - Epistemic uncertainty (model uncertainty)
    - Calibration of confidence scores
    """
    
    def estimate_uncertainty(self, inference_result: InferenceResult) -> UncertaintyEstimate:
        """Estimate uncertainty for inference result."""
        # Placeholder: in real implementation, would use ensemble methods,
        # MC dropout, or other uncertainty quantification techniques
        
        if inference_result.confidence is not None:
            # Simple inverse relationship
            uncertainty = 1.0 - inference_result.confidence
        else:
            uncertainty = 0.5  # Unknown
        
        return UncertaintyEstimate(
            value=uncertainty,
            type="epistemic",
            metadata={"model_id": inference_result.model_id}
        )


# ============================================================================
# MODEL REGISTRY
# ============================================================================

class ModelRegistry:
    """
    Registry for AI models.
    
    Manages model lifecycle:
    - Registration
    - Validation
    - Status tracking
    - Version management
    """
    
    def __init__(self):
        """Initialize empty registry."""
        self.models: Dict[str, ModelContract] = {}
    
    def register(self, model: ModelContract) -> None:
        """Register a new model."""
        if model.id in self.models:
            raise ValueError(f"Model {model.id} already registered")
        self.models[model.id] = model
    
    def get(self, model_id: str) -> Optional[ModelContract]:
        """Get model by ID."""
        return self.models.get(model_id)
    
    def update_status(self, model_id: str, status: ModelStatus) -> None:
        """Update model status."""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")
        self.models[model_id].status = status
    
    def list_models(self, status: Optional[ModelStatus] = None) -> List[ModelContract]:
        """List models, optionally filtered by status."""
        if status is None:
            return list(self.models.values())
        return [m for m in self.models.values() if m.status == status]
