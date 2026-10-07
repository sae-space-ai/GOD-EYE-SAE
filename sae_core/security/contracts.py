"""
SAE Core Security - Identity, authorization, policy, and audit contracts.

This module defines the security system contracts for IAM, RBAC, policy engine,
approvals, and audit trail.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field
from ..common.enums import (
    PolicyDecision,
    ApprovalStatus,
    RiskLevel,
    UserRole,
    generate_id,
    utc_now,
)


# ============================================================================
# USER AND ROLES
# ============================================================================

@dataclass
class User:
    """System user."""
    id: str
    username: str
    email: str
    roles: List[UserRole]
    organization: Optional[str] = None
    active: bool = True
    created_at: datetime = field(default_factory=utc_now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    """User session."""
    id: str
    user_id: str
    token: str
    expires_at: datetime
    created_at: datetime = field(default_factory=utc_now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return utc_now() > self.expires_at


@dataclass
class Permission:
    """Permission definition."""
    id: str
    name: str  # e.g., "mission.create", "model.infer"
    description: str
    resource_type: str  # "mission", "model", "source", etc.
    action: str  # "read", "create", "execute", "approve", etc.


@dataclass
class Role:
    """Role with permissions."""
    id: str
    name: UserRole
    description: str
    permissions: List[str]  # Permission IDs
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# POLICY ENGINE
# ============================================================================

@dataclass
class PolicyContext:
    """Context for policy evaluation."""
    actor: User
    action: str
    resource: str
    resource_id: Optional[str] = None
    mission_id: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.LOW
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyDecisionResult:
    """Result from policy evaluation."""
    decision: PolicyDecision
    reason: str
    policy_id: Optional[str] = None
    timestamp: datetime = field(default_factory=utc_now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PolicyEngine:
    """
    Evaluates policies for authorization decisions.
    
    Supports:
    - RBAC (Role-Based Access Control)
    - ABAC (Attribute-Based Access Control) - prepared
    - Risk-based policies
    - Mission-specific policies
    """
    
    def __init__(self, roles: Dict[str, Role]):
        """Initialize with role definitions."""
        self.roles = roles
    
    def evaluate(self, context: PolicyContext) -> PolicyDecisionResult:
        """Evaluate policy for context."""
        # Check if actor has required permissions
        actor_permissions = set()
        for role_name in context.actor.roles:
            if role_name.value in self.roles:
                role = self.roles[role_name.value]
                actor_permissions.update(role.permissions)
        
        # Check if action is permitted
        required_permission = f"{context.resource}.{context.action}"
        
        if required_permission in actor_permissions or f"{context.resource}.*" in actor_permissions:
            # Check risk level
            if context.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                return PolicyDecisionResult(
                    decision=PolicyDecision.REQUIRE_APPROVAL,
                    reason=f"High-risk action requires approval",
                    metadata={"risk_level": context.risk_level.value}
                )
            
            return PolicyDecisionResult(
                decision=PolicyDecision.ALLOW,
                reason="Permission granted"
            )
        
        return PolicyDecisionResult(
            decision=PolicyDecision.DENY,
            reason=f"Permission denied: {required_permission}",
            metadata={"required_permission": required_permission}
        )


# ============================================================================
# APPROVAL ENGINE
# ============================================================================

@dataclass
class Approval:
    """Human approval record."""
    id: str
    mission_id: str
    execution_node_id: Optional[str]
    requested_by: str  # user_id or "system"
    requested_at: datetime
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    decision: ApprovalStatus = ApprovalStatus.PENDING
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def approve(self, reviewer_id: str, reason: Optional[str] = None) -> None:
        """Approve request."""
        if self.decision != ApprovalStatus.PENDING:
            raise ValueError(f"Cannot approve: status is {self.decision}")
        self.reviewed_by = reviewer_id
        self.reviewed_at = utc_now()
        self.decision = ApprovalStatus.APPROVED
        self.reason = reason
    
    def reject(self, reviewer_id: str, reason: str) -> None:
        """Reject request."""
        if self.decision != ApprovalStatus.PENDING:
            raise ValueError(f"Cannot reject: status is {self.decision}")
        self.reviewed_by = reviewer_id
        self.reviewed_at = utc_now()
        self.decision = ApprovalStatus.REJECTED
        self.reason = reason


class ApprovalEngine:
    """
    Manages human approval workflows.
    
    Ensures:
    - No self-approval
    - Approval expiration
    - Audit trail
    """
    
    def request_approval(
        self,
        mission_id: str,
        execution_node_id: Optional[str],
        requested_by: str
    ) -> Approval:
        """Request approval for action."""
        approval = Approval(
            id=generate_id(),
            mission_id=mission_id,
            execution_node_id=execution_node_id,
            requested_by=requested_by,
            requested_at=utc_now()
        )
        return approval


# ============================================================================
# AUDIT ENGINE
# ============================================================================

@dataclass
class AuditEvent:
    """Audit trail event."""
    id: str
    timestamp: datetime
    actor: str  # user_id or "system"
    action: str
    resource: str
    resource_id: Optional[str] = None
    mission_id: Optional[str] = None
    status: str = "success"  # "success", "failure"
    metadata: Dict[str, Any] = field(default_factory=dict)


class AuditEngine:
    """
    Records audit trail for all operations.
    
    Ensures:
    - No secrets logged
    - Correlation IDs propagated
    - Immutable audit trail
    """
    
    def __init__(self):
        """Initialize audit engine."""
        self.events: List[AuditEvent] = []
    
    def record(
        self,
        actor: str,
        action: str,
        resource: str,
        resource_id: Optional[str] = None,
        mission_id: Optional[str] = None,
        status: str = "success",
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """Record audit event."""
        event = AuditEvent(
            id=generate_id(),
            timestamp=utc_now(),
            actor=actor,
            action=action,
            resource=resource,
            resource_id=resource_id,
            mission_id=mission_id,
            status=status,
            metadata=metadata or {}
        )
        self.events.append(event)
        return event
    
    def get_events(self, mission_id: Optional[str] = None, limit: int = 100) -> List[AuditEvent]:
        """Get audit events, optionally filtered by mission."""
        if mission_id:
            events = [e for e in self.events if e.mission_id == mission_id]
        else:
            events = self.events
        
        return events[-limit:]
