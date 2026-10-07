"""
SAE Intelligence Core - Central contracts and enums.

This module defines the foundational types, enums, and error classes
used throughout the SAE Intelligence Core system.
"""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field
import uuid


# ============================================================================
# MISSION STATES
# ============================================================================

class MissionStatus(str, Enum):
    """Mission lifecycle states."""
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    WAITING_FOR_DATA = "WAITING_FOR_DATA"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# ============================================================================
# EXECUTION NODE STATES
# ============================================================================

class ExecutionNodeStatus(str, Enum):
    """Execution graph node states."""
    PENDING = "PENDING"
    BLOCKED = "BLOCKED"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    SKIPPED = "SKIPPED"


# ============================================================================
# SOURCE STATES
# ============================================================================

class SourceStatus(str, Enum):
    """Data source integration states."""
    INTEGRATED_VERIFIED = "INTEGRATED_VERIFIED"
    INTEGRATED_UNVERIFIED = "INTEGRATED_UNVERIFIED"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    LOADING = "LOADING"
    DISABLED = "DISABLED"


# ============================================================================
# MODEL STATES
# ============================================================================

class ModelStatus(str, Enum):
    """AI model lifecycle states."""
    REGISTERED = "REGISTERED"
    VALIDATING = "VALIDATING"
    VALIDATED = "VALIDATED"
    TRAINING = "TRAINING"
    READY = "READY"
    DEGRADED = "DEGRADED"
    DISABLED = "DISABLED"
    FAILED = "FAILED"


# ============================================================================
# EPISTEMIC TYPES
# ============================================================================

class EpistemicType(str, Enum):
    """Classification of information certainty."""
    OBSERVED = "OBSERVED"           # Direct measurement
    DERIVED = "DERIVED"             # Calculated from observations
    INFERRED = "INFERRED"           # ML/AI inference
    PREDICTED = "PREDICTED"         # Future forecast
    SIMULATED = "SIMULATED"         # Hypothetical scenario


# ============================================================================
# RISK LEVELS
# ============================================================================

class RiskLevel(str, Enum):
    """Mission and operation risk classification."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# ============================================================================
# DATA CLASSIFICATION
# ============================================================================

class DataClassification(str, Enum):
    """Data sensitivity classification."""
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    RESTRICTED = "RESTRICTED"
    SENSITIVE = "SENSITIVE"


# ============================================================================
# APPROVAL STATES
# ============================================================================

class ApprovalStatus(str, Enum):
    """Human approval workflow states."""
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


# ============================================================================
# POLICY DECISIONS
# ============================================================================

class PolicyDecision(str, Enum):
    """Policy engine decision outcomes."""
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


# ============================================================================
# USER ROLES
# ============================================================================

class UserRole(str, Enum):
    """System user roles."""
    VIEWER = "VIEWER"
    ANALYST = "ANALYST"
    OPERATOR = "OPERATOR"
    MISSION_MANAGER = "MISSION_MANAGER"
    SCIENTIST = "SCIENTIST"
    AUDITOR = "AUDITOR"
    ADMIN = "ADMIN"


# ============================================================================
# INTENT TYPES
# ============================================================================

class IntentType(str, Enum):
    """User intent classifications."""
    EXPLORE_AREA = "EXPLORE_AREA"
    ANALYZE_CHANGE = "ANALYZE_CHANGE"
    ASSESS_RISK = "ASSESS_RISK"
    SEARCH_EVIDENCE = "SEARCH_EVIDENCE"
    RUN_INFERENCE = "RUN_INFERENCE"
    PLAN_ACQUISITION = "PLAN_ACQUISITION"
    PREDICT_EVENT = "PREDICT_EVENT"
    COMPARE_DATES = "COMPARE_DATES"
    CREATE_MISSION = "CREATE_MISSION"
    EXPORT_RESULT = "EXPORT_RESULT"


# ============================================================================
# JOB STATES
# ============================================================================

class JobStatus(str, Enum):
    """Async job lifecycle states."""
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# ============================================================================
# TOOL TYPES
# ============================================================================

class ToolType(str, Enum):
    """Execution tool classification."""
    READ_ONLY = "READ_ONLY"
    COMPUTE = "COMPUTE"
    WRITE = "WRITE"
    EXTERNAL_ACTION = "EXTERNAL_ACTION"


# ============================================================================
# EVENT TYPES
# ============================================================================

class EventType(str, Enum):
    """System event classifications."""
    SOURCE_DATA_RECEIVED = "SOURCE_DATA_RECEIVED"
    NEW_OBSERVATION = "NEW_OBSERVATION"
    MODEL_INFERENCE_STARTED = "MODEL_INFERENCE_STARTED"
    MODEL_INFERENCE_COMPLETED = "MODEL_INFERENCE_COMPLETED"
    MODEL_INFERENCE_FAILED = "MODEL_INFERENCE_FAILED"
    ANOMALY_DETECTED = "ANOMALY_DETECTED"
    PREDICTION_CREATED = "PREDICTION_CREATED"
    EVIDENCE_CAPTURED = "EVIDENCE_CAPTURED"
    EVIDENCE_VERIFIED = "EVIDENCE_VERIFIED"
    MISSION_CREATED = "MISSION_CREATED"
    MISSION_UPDATED = "MISSION_UPDATED"
    MISSION_COMPLETED = "MISSION_COMPLETED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVAL_RESOLVED = "APPROVAL_RESOLVED"
    ACQUISITION_WINDOW_FOUND = "ACQUISITION_WINDOW_FOUND"


# ============================================================================
# ERROR CLASSES
# ============================================================================

class SAEError(Exception):
    """Base exception for SAE Core."""
    def __init__(self, message: str, code: str = "SAE_ERROR", metadata: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.metadata = metadata or {}


class ValidationError(SAEError):
    """Validation error."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="VALIDATION_ERROR", metadata=metadata)


class AuthorizationError(SAEError):
    """Authorization error."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="AUTHORIZATION_ERROR", metadata=metadata)


class PolicyDeniedError(SAEError):
    """Policy denial error."""
    def __init__(self, message: str, policy_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="POLICY_DENIED", metadata={**(metadata or {}), "policy_id": policy_id})
        self.policy_id = policy_id


class ApprovalRequiredError(SAEError):
    """Approval required error."""
    def __init__(self, message: str, approval_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="APPROVAL_REQUIRED", metadata={**(metadata or {}), "approval_id": approval_id})
        self.approval_id = approval_id


class SourceUnavailableError(SAEError):
    """Source unavailable error."""
    def __init__(self, message: str, source_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="SOURCE_UNAVAILABLE", metadata={**(metadata or {}), "source_id": source_id})
        self.source_id = source_id


class ModelUnavailableError(SAEError):
    """Model unavailable error."""
    def __init__(self, message: str, model_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="MODEL_UNAVAILABLE", metadata={**(metadata or {}), "model_id": model_id})
        self.model_id = model_id


class MissionStateError(SAEError):
    """Mission state transition error."""
    def __init__(self, message: str, mission_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="MISSION_STATE_ERROR", metadata={**(metadata or {}), "mission_id": mission_id})
        self.mission_id = mission_id


class ExecutionError(SAEError):
    """Execution error."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="EXECUTION_ERROR", metadata=metadata)


class EvidenceError(SAEError):
    """Evidence error."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="EVIDENCE_ERROR", metadata=metadata)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_id() -> str:
    """Generate a new UUID."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.utcnow()
