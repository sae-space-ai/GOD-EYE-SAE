"""
SAE AI Governance

Handles permissions, policies, risk classification, and audit for AI operations.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AIRiskLevel(str, Enum):
    """AI operation risk levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AIPermission(str, Enum):
    """AI-specific permissions."""
    # Command permissions
    AI_COMMAND_CREATE = "ai.command.create"
    AI_COMMAND_EXECUTE = "ai.command.execute"
    AI_COMMAND_READ = "ai.command.read"
    
    # Model permissions
    AI_MODEL_REGISTER = "ai.model.register"
    AI_MODEL_VALIDATE = "ai.model.validate"
    AI_MODEL_DEPLOY = "ai.model.deploy"
    AI_MODEL_DISABLE = "ai.model.disable"
    AI_MODEL_READ = "ai.model.read"
    
    # Training permissions
    AI_TRAINING_CREATE = "ai.training.create"
    AI_TRAINING_APPROVE = "ai.training.approve"
    AI_TRAINING_READ = "ai.training.read"
    
    # Dataset permissions
    AI_DATASET_REGISTER = "ai.dataset.register"
    AI_DATASET_VALIDATE = "ai.dataset.validate"
    AI_DATASET_READ = "ai.dataset.read"
    
    # Inference permissions
    AI_INFERENCE_EXECUTE = "ai.inference.execute"
    AI_INFERENCE_READ = "ai.inference.read"
    
    # Evaluation permissions
    AI_EVALUATION_CREATE = "ai.evaluation.create"
    AI_EVALUATION_READ = "ai.evaluation.read"


class AIRiskClassifier:
    """Classifies AI operations by risk level."""
    
    # Default risk classifications
    RISK_MAP = {
        # Low risk operations
        "ai.command.read": AIRiskLevel.LOW,
        "ai.model.read": AIRiskLevel.LOW,
        "ai.inference.read": AIRiskLevel.LOW,
        "ai.training.read": AIRiskLevel.LOW,
        "ai.dataset.read": AIRiskLevel.LOW,
        "ai.evaluation.read": AIRiskLevel.LOW,
        
        # Medium risk operations
        "ai.command.create": AIRiskLevel.MEDIUM,
        "ai.command.execute": AIRiskLevel.MEDIUM,
        "ai.inference.execute": AIRiskLevel.MEDIUM,
        "ai.dataset.register": AIRiskLevel.MEDIUM,
        "ai.dataset.validate": AIRiskLevel.MEDIUM,
        "ai.model.register": AIRiskLevel.MEDIUM,
        "ai.model.validate": AIRiskLevel.MEDIUM,
        "ai.evaluation.create": AIRiskLevel.MEDIUM,
        
        # High risk operations
        "ai.model.deploy": AIRiskLevel.HIGH,
        "ai.model.disable": AIRiskLevel.HIGH,
        "ai.training.create": AIRiskLevel.HIGH,
        "ai.training.approve": AIRiskLevel.HIGH,
        
        # Critical risk operations
        # (Would be defined based on specific use cases)
    }
    
    def classify(
        self,
        permission: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AIRiskLevel:
        """
        Classify operation risk level.
        
        Args:
            permission: Permission being requested
            context: Optional context that might affect risk
        
        Returns:
            AIRiskLevel
        """
        # Default classification
        risk = self.RISK_MAP.get(permission, AIRiskLevel.MEDIUM)
        
        # Adjust based on context
        if context:
            # High-risk mission context
            if context.get("mission_risk_level") in ["HIGH", "CRITICAL"]:
                if risk == AIRiskLevel.MEDIUM:
                    risk = AIRiskLevel.HIGH
            
            # Sensitive data operations
            if context.get("sensitive_data"):
                if risk == AIRiskLevel.MEDIUM:
                    risk = AIRiskLevel.HIGH
            
            # External actions
            if context.get("external_action"):
                risk = AIRiskLevel.HIGH
        
        logger.debug(f"Risk classified for {permission}: {risk.value}")
        
        return risk


class AIPolicyEngine:
    """Policy engine for AI operations."""
    
    def __init__(self, risk_classifier: AIRiskClassifier):
        self.risk_classifier = risk_classifier
    
    def evaluate(
        self,
        actor: str,
        permission: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate policy for AI operation.
        
        Args:
            actor: User ID
            permission: Permission being requested
            context: Operation context
        
        Returns:
            Dict with 'allowed', 'requires_approval', 'reason'
        """
        # Classify risk
        risk = self.risk_classifier.classify(permission, context)
        
        # Check if approval is required
        requires_approval = risk in [AIRiskLevel.HIGH, AIRiskLevel.CRITICAL]
        
        # In real implementation, would check:
        # - Actor permissions
        # - Resource ownership
        # - Time-based policies
        # - Quota limits
        # - Compliance requirements
        
        allowed = True  # Simplified - in real implementation would check permissions
        
        result = {
            "allowed": allowed,
            "requires_approval": requires_approval,
            "risk_level": risk.value,
            "reason": f"Risk level: {risk.value}"
        }
        
        logger.info(
            f"Policy evaluated for {actor} - {permission}: "
            f"allowed={allowed}, requires_approval={requires_approval}, risk={risk.value}"
        )
        
        return result


class AIProvenanceTracker:
    """Tracks provenance for AI operations."""
    
    def __init__(self):
        self.provenance_records: List[Dict[str, Any]] = []
    
    def record(
        self,
        operation_id: str,
        operation_type: str,
        actor: str,
        model_id: Optional[str] = None,
        dataset_id: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
        outputs: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        correlation_id: str = ""
    ) -> None:
        """Record provenance for an operation."""
        record = {
            "operation_id": operation_id,
            "operation_type": operation_type,
            "actor": actor,
            "model_id": model_id,
            "dataset_id": dataset_id,
            "inputs": inputs,
            "outputs": outputs,
            "parameters": parameters,
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.provenance_records.append(record)
        
        logger.debug(f"Provenance recorded for {operation_id}")
    
    def get_provenance(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get provenance for an operation."""
        for record in self.provenance_records:
            if record["operation_id"] == operation_id:
                return record
        return None
    
    def get_provenance_chain(self, correlation_id: str) -> List[Dict[str, Any]]:
        """Get full provenance chain for a correlation ID."""
        return [
            record for record in self.provenance_records
            if record["correlation_id"] == correlation_id
        ]


class AIGovernance:
    """
    Main AI governance module.
    
    Integrates permissions, policies, risk classification, provenance, and audit.
    """
    
    def __init__(self, audit_engine=None):
        self.audit_engine = audit_engine
        self.risk_classifier = AIRiskClassifier()
        self.policy_engine = AIPolicyEngine(self.risk_classifier)
        self.provenance_tracker = AIProvenanceTracker()
    
    def check_permission(
        self,
        actor: str,
        permission: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Check if actor has permission for operation."""
        return self.policy_engine.evaluate(actor, permission, context)
    
    def record_provenance(
        self,
        operation_id: str,
        operation_type: str,
        actor: str,
        **kwargs
    ) -> None:
        """Record operation provenance."""
        self.provenance_tracker.record(
            operation_id=operation_id,
            operation_type=operation_type,
            actor=actor,
            **kwargs
        )
    
    def audit_operation(
        self,
        actor: str,
        action: str,
        resource: str,
        resource_id: str,
        status: str = "success",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Audit an AI operation."""
        if self.audit_engine:
            self.audit_engine.record(
                actor=actor,
                action=action,
                resource=resource,
                resource_id=resource_id,
                status=status,
                metadata=metadata or {}
            )
    
    def get_risk_level(self, permission: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Get risk level for an operation."""
        return self.risk_classifier.classify(permission, context).value
