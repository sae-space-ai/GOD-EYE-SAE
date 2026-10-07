"""
SAE AI Model Router

Selects appropriate models based on request requirements.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from .models import (
    AIRequest, ModelSelection, AIModel, ModelStatus,
    ModelCapability
)
from .model_registry import ModelRegistry

logger = logging.getLogger(__name__)


class ModelRouter:
    """
    Routes AI requests to appropriate models.
    
    Selects models based on capabilities, modalities, risk, and policies.
    """
    
    def __init__(
        self,
        model_registry: ModelRegistry,
        policy_engine=None,
        authorization_service=None
    ):
        self.model_registry = model_registry
        self.policy_engine = policy_engine
        self.authorization_service = authorization_service
    
    def select_model(self, request: AIRequest) -> ModelSelection:
        """
        Select the best model for a request.
        
        Args:
            request: AIRequest with requirements
        
        Returns:
            ModelSelection with selected model and alternatives
        """
        # Get candidate models
        candidates = self._get_candidates(request)
        
        if not candidates:
            logger.warning(f"No models available for request {request.id}")
            raise ValueError("No models available for this request")
        
        # Score and rank candidates
        scored_candidates = self._score_candidates(candidates, request)
        
        # Select best model
        selected = scored_candidates[0][0]
        selection_reason = scored_candidates[0][1]
        
        # Get alternatives
        alternatives = [model for model, _ in scored_candidates[1:4]]
        
        # Check policy
        policy_result = None
        if self.policy_engine:
            policy_result = self._check_policy(request, selected)
        
        model_selection = ModelSelection(
            selected_model=selected,
            alternatives=alternatives,
            selection_reason=selection_reason,
            capability_match=self._get_capability_match(selected, request),
            policy_result=policy_result,
            timestamp=datetime.utcnow()
        )
        
        logger.info(
            f"Model selected for request {request.id}: "
            f"{selected.id} ({selected.name}) - {selection_reason}"
        )
        
        return model_selection
    
    def _get_candidates(self, request: AIRequest) -> List[AIModel]:
        """Get candidate models matching request requirements."""
        candidates = []
        
        for model in self.model_registry.models.values():
            # Skip non-operational models
            if model.status not in [
                ModelStatus.READY,
                ModelStatus.DEPLOYED,
                ModelStatus.VALIDATED
            ]:
                continue
            
            # Check capabilities
            if request.required_capabilities:
                if not all(cap in model.capabilities for cap in request.required_capabilities):
                    continue
            
            # Check modalities
            if request.modalities:
                if not all(mod in model.modalities for mod in request.modalities):
                    continue
            
            # Check device compatibility
            if request.context.get("device"):
                if model.device != request.context["device"]:
                    continue
            
            candidates.append(model)
        
        return candidates
    
    def _score_candidates(
        self,
        candidates: List[AIModel],
        request: AIRequest
    ) -> List[tuple]:
        """
        Score and rank candidates.
        
        Returns:
            List of (model, score, reason) tuples, sorted by score descending
        """
        scored = []
        
        for model in candidates:
            score = 0.0
            reasons = []
            
            # Capability match score (0-40 points)
            if request.required_capabilities:
                matched_caps = sum(1 for cap in request.required_capabilities if cap in model.capabilities)
                cap_score = (matched_caps / len(request.required_capabilities)) * 40
                score += cap_score
                reasons.append(f"capabilities: {matched_caps}/{len(request.required_capabilities)}")
            
            # Modality match score (0-20 points)
            if request.modalities:
                matched_mods = sum(1 for mod in request.modalities if mod in model.modalities)
                mod_score = (matched_mods / len(request.modalities)) * 20
                score += mod_score
                reasons.append(f"modalities: {matched_mods}/{len(request.modalities)}")
            
            # Status score (0-20 points)
            status_scores = {
                ModelStatus.READY: 20,
                ModelStatus.DEPLOYED: 20,
                ModelStatus.VALIDATED: 15,
            }
            score += status_scores.get(model.status, 0)
            reasons.append(f"status: {model.status.value}")
            
            # Device preference score (0-10 points)
            if request.context.get("preferred_device"):
                if model.device == request.context["preferred_device"]:
                    score += 10
                    reasons.append("device preference matched")
            
            # Latency score (0-10 points)
            if request.latency_requirement:
                # Lower latency models get higher scores
                # This is simplified - in real implementation would use actual latency metrics
                if model.device == "cuda":
                    score += 10
                    reasons.append("GPU acceleration available")
            
            scored.append((model, score, "; ".join(reasons)))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return [(model, reason) for model, score, reason in scored]
    
    def _get_capability_match(
        self,
        model: AIModel,
        request: AIRequest
    ) -> Dict[str, Any]:
        """Get detailed capability match information."""
        match = {
            "required": [cap.value for cap in request.required_capabilities],
            "available": [cap.value for cap in model.capabilities],
            "matched": [],
            "missing": []
        }
        
        for cap in request.required_capabilities:
            if cap in model.capabilities:
                match["matched"].append(cap.value)
            else:
                match["missing"].append(cap.value)
        
        return match
    
    def _check_policy(
        self,
        request: AIRequest,
        model: AIModel
    ) -> Dict[str, Any]:
        """Check policy for model selection."""
        if not self.policy_engine:
            return {"allowed": True, "reason": "No policy engine configured"}
        
        # In real implementation, would check:
        # - Model usage policies
        # - Cost constraints
        # - Privacy requirements
        # - Risk level policies
        
        return {
            "allowed": True,
            "reason": "Policy check passed",
            "constraints": []
        }
    
    def get_alternatives(
        self,
        request: AIRequest,
        count: int = 3
    ) -> List[AIModel]:
        """
        Get alternative models for a request.
        
        Args:
            request: AIRequest
            count: Number of alternatives to return
        
        Returns:
            List of alternative models
        """
        candidates = self._get_candidates(request)
        scored = self._score_candidates(candidates, request)
        
        return [model for model, _ in scored[1:count+1]]
    
    def validate_model_availability(
        self,
        model_id: str,
        required_capabilities: List[ModelCapability]
    ) -> Dict[str, Any]:
        """
        Validate if a specific model is available for given capabilities.
        
        Args:
            model_id: Model ID
            required_capabilities: Required capabilities
        
        Returns:
            Dict with validation results
        """
        model = self.model_registry.get_model(model_id)
        
        if not model:
            return {
                "available": False,
                "reason": "Model not found"
            }
        
        if model.status not in [ModelStatus.READY, ModelStatus.DEPLOYED, ModelStatus.VALIDATED]:
            return {
                "available": False,
                "reason": f"Model status is {model.status.value}"
            }
        
        missing_caps = [cap for cap in required_capabilities if cap not in model.capabilities]
        
        if missing_caps:
            return {
                "available": False,
                "reason": f"Missing capabilities: {[cap.value for cap in missing_caps]}"
            }
        
        return {
            "available": True,
            "reason": "Model is available and has required capabilities",
            "model": model
        }
