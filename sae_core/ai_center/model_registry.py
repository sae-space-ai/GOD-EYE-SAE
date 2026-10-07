"""
SAE AI Model Registry

Manages model registration, lifecycle, and health monitoring.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from .models import AIModel, ModelStatus, ModelCapability, ModelType

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Registry for AI models.
    
    Manages model lifecycle from registration to deployment/retirement.
    """
    
    def __init__(self):
        self.models: Dict[str, AIModel] = {}
        self.model_versions: Dict[str, List[str]] = {}  # model_id -> [version_ids]
    
    def register_model(self, model: AIModel) -> None:
        """
        Register a new model.
        
        Args:
            model: AIModel to register
        
        Raises:
            ValueError: If model ID already exists
        """
        if model.id in self.models:
            raise ValueError(f"Model {model.id} already registered")
        
        self.models[model.id] = model
        
        # Track versions
        if model.id not in self.model_versions:
            self.model_versions[model.id] = []
        self.model_versions[model.id].append(model.version)
        
        logger.info(f"Model registered: {model.id} v{model.version} ({model.name})")
    
    def get_model(self, model_id: str) -> Optional[AIModel]:
        """Get model by ID."""
        return self.models.get(model_id)
    
    def update_model_status(self, model_id: str, status: ModelStatus) -> None:
        """
        Update model status.
        
        Args:
            model_id: Model ID
            status: New status
        
        Raises:
            ValueError: If model not found
        """
        model = self.models.get(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")
        
        old_status = model.status
        model.status = status
        model.updated_at = datetime.utcnow()
        
        logger.info(f"Model {model_id} status changed: {old_status} -> {status}")
    
    def update_model_metadata(self, model_id: str, metadata: Dict[str, Any]) -> None:
        """Update model metadata."""
        model = self.models.get(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")
        
        model.metadata.update(metadata)
        model.updated_at = datetime.utcnow()
    
    def list_models(
        self,
        status: Optional[ModelStatus] = None,
        capability: Optional[ModelCapability] = None,
        model_type: Optional[ModelType] = None
    ) -> List[AIModel]:
        """
        List models with optional filters.
        
        Args:
            status: Filter by status
            capability: Filter by capability
            model_type: Filter by model type
        
        Returns:
            List of matching models
        """
        models = list(self.models.values())
        
        if status:
            models = [m for m in models if m.status == status]
        
        if capability:
            models = [m for m in models if capability in m.capabilities]
        
        if model_type:
            models = [m for m in models if m.model_type == model_type]
        
        return models
    
    def get_model_versions(self, model_id: str) -> List[str]:
        """Get all versions of a model."""
        return self.model_versions.get(model_id, [])
    
    def get_latest_version(self, model_id: str) -> Optional[str]:
        """Get latest version of a model."""
        versions = self.model_versions.get(model_id, [])
        return versions[-1] if versions else None
    
    def validate_model(self, model_id: str) -> Dict[str, Any]:
        """
        Validate model configuration and readiness.
        
        Returns:
            Dict with validation results
        """
        model = self.models.get(model_id)
        if not model:
            return {"valid": False, "errors": ["Model not found"]}
        
        errors = []
        warnings = []
        
        # Check basic fields
        if not model.name:
            errors.append("Model name is required")
        
        if not model.provider:
            errors.append("Model provider is required")
        
        if not model.version:
            errors.append("Model version is required")
        
        if not model.capabilities:
            warnings.append("Model has no capabilities defined")
        
        if not model.modalities:
            warnings.append("Model has no modalities defined")
        
        # Check status-specific requirements
        if model.status == ModelStatus.READY:
            if not model.checkpoint and model.model_type != ModelType.LLM:
                warnings.append("READY model should have checkpoint path")
        
        valid = len(errors) == 0
        
        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings
        }
    
    def get_model_health(self, model_id: str) -> Dict[str, Any]:
        """
        Get model health status.
        
        Returns:
            Dict with health information
        """
        model = self.models.get(model_id)
        if not model:
            return {"status": "NOT_FOUND", "healthy": False}
        
        # Determine health based on status
        healthy_statuses = [
            ModelStatus.READY,
            ModelStatus.DEPLOYED,
            ModelStatus.VALIDATED
        ]
        
        degraded_statuses = [
            ModelStatus.DEGRADED,
            ModelStatus.TRAINING
        ]
        
        unhealthy_statuses = [
            ModelStatus.FAILED,
            ModelStatus.BLOCKED,
            ModelStatus.DISABLED
        ]
        
        if model.status in healthy_statuses:
            health_status = "HEALTHY"
            healthy = True
        elif model.status in degraded_statuses:
            health_status = "DEGRADED"
            healthy = True  # Still operational but degraded
        elif model.status in unhealthy_statuses:
            health_status = "UNHEALTHY"
            healthy = False
        else:
            health_status = "UNKNOWN"
            healthy = False
        
        return {
            "status": health_status,
            "healthy": healthy,
            "model_status": model.status.value,
            "device": model.device,
            "last_updated": model.updated_at.isoformat()
        }
    
    def disable_model(self, model_id: str, reason: str = "") -> None:
        """Disable a model."""
        model = self.models.get(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")
        
        model.status = ModelStatus.DISABLED
        model.updated_at = datetime.utcnow()
        model.metadata["disable_reason"] = reason
        
        logger.info(f"Model {model_id} disabled: {reason}")
    
    def retire_model(self, model_id: str, reason: str = "") -> None:
        """Retire a model."""
        model = self.models.get(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")
        
        model.status = ModelStatus.RETIRED
        model.updated_at = datetime.utcnow()
        model.metadata["retire_reason"] = reason
        
        logger.info(f"Model {model_id} retired: {reason}")
    
    def get_models_by_capability(self, capability: ModelCapability) -> List[AIModel]:
        """Get all models with a specific capability."""
        return [
            model for model in self.models.values()
            if capability in model.capabilities and model.status in [
                ModelStatus.READY,
                ModelStatus.DEPLOYED,
                ModelStatus.VALIDATED
            ]
        ]
    
    def get_models_by_modality(self, modality: str) -> List[AIModel]:
        """Get all models supporting a specific modality."""
        return [
            model for model in self.models.values()
            if modality in model.modalities and model.status in [
                ModelStatus.READY,
                ModelStatus.DEPLOYED,
                ModelStatus.VALIDATED
            ]
        ]
