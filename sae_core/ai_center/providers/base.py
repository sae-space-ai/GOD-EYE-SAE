"""
Base provider and adapter interfaces.
"""

from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    def __init__(self, provider_id: str, config: Dict[str, Any]):
        self.provider_id = provider_id
        self.config = config
    
    @abstractmethod
    def health(self) -> Dict[str, Any]:
        """Check provider health."""
        pass
    
    @abstractmethod
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        pass
    
    @abstractmethod
    def get_capabilities(self, model_id: str) -> List[str]:
        """Get model capabilities."""
        pass
    
    @abstractmethod
    def infer(self, model_id: str, inputs: Dict[str, Any], parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run inference."""
        pass
    
    def embed(self, model_id: str, texts: List[str]) -> List[List[float]]:
        """Generate embeddings (optional)."""
        raise NotImplementedError(f"{self.__class__.__name__} does not support embeddings")
    
    def validate_input(self, model_id: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input (optional)."""
        return {"valid": True, "errors": []}
    
    def validate_output(self, model_id: str, outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate output (optional)."""
        return {"valid": True, "errors": []}
    
    def train(self, model_id: str, dataset_id: str, config: Dict[str, Any]) -> str:
        """Start training (optional)."""
        raise NotImplementedError(f"{self.__class__.__name__} does not support training")
    
    def fine_tune(self, model_id: str, dataset_id: str, config: Dict[str, Any]) -> str:
        """Start fine-tuning (optional)."""
        raise NotImplementedError(f"{self.__class__.__name__} does not support fine-tuning")
    
    def cancel_training(self, job_id: str) -> bool:
        """Cancel training job (optional)."""
        raise NotImplementedError(f"{self.__class__.__name__} does not support training cancellation")
    
    def training_status(self, job_id: str) -> Dict[str, Any]:
        """Get training job status (optional)."""
        raise NotImplementedError(f"{self.__class__.__name__} does not support training status")


class ModelAdapter:
    """Adapter for a specific model within a provider."""
    
    def __init__(self, provider: AIProvider, model_id: str):
        self.provider = provider
        self.model_id = model_id
    
    def health(self) -> Dict[str, Any]:
        """Check model health."""
        return self.provider.health()
    
    def infer(self, inputs: Dict[str, Any], parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run inference."""
        return self.provider.infer(self.model_id, inputs, parameters)
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings."""
        return self.provider.embed(self.model_id, texts)
    
    def validate_input(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input."""
        return self.provider.validate_input(self.model_id, inputs)
    
    def validate_output(self, outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate output."""
        return self.provider.validate_output(self.model_id, outputs)
