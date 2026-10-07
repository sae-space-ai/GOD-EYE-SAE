"""
SAE Core Security - Authorization service.

This module provides authorization functionality with RBAC and ABAC.
"""

from typing import Optional, List
from ..common.enums import PolicyDecision, RiskLevel, UserRole
from ..persistence import User, Mission
from .contracts import PolicyContext, PolicyDecisionResult, PolicyEngine, Role, Permission


class AuthorizationService:
    """Authorization service for RBAC and ABAC."""
    
    def __init__(self, policy_engine: PolicyEngine):
        """Initialize authorization service."""
        self.policy_engine = policy_engine
    
    def check_permission(self, user: User, action: str, resource: str) -> bool:
        """Check if user has permission for action on resource."""
        # Check RBAC
        user_permissions = set()
        for role_name in user.roles:
            if role_name in self.policy_engine.roles:
                role = self.policy_engine.roles[role_name]
                user_permissions.update(role.permissions)
        
        required_permission = f"{resource}.{action}"
        return required_permission in user_permissions or f"{resource}.*" in user_permissions
    
    def check_mission_access(self, user: User, mission: Mission) -> bool:
        """Check if user can access mission (ABAC)."""
        # Check ownership
        if mission.created_by == user.id:
            return True
        
        # Check organization
        if user.organization and hasattr(mission, 'organization'):
            if mission.organization == user.organization:
                return True
        
        # Check role-based access
        if UserRole.ADMIN.value in user.roles:
            return True
        
        if UserRole.MISSION_MANAGER.value in user.roles:
            return True
        
        return False
    
    def evaluate_policy(
        self,
        user: User,
        action: str,
        resource: str,
        resource_id: Optional[str] = None,
        mission: Optional[Mission] = None,
        risk_level: RiskLevel = RiskLevel.LOW,
        context: Optional[dict] = None
    ) -> PolicyDecisionResult:
        """Evaluate policy for an action."""
        policy_context = PolicyContext(
            actor=user,
            action=action,
            resource=resource,
            resource_id=resource_id,
            mission_id=mission.id if mission else None,
            risk_level=risk_level,
            context=context or {}
        )
        
        # Check RBAC first
        if not self.check_permission(user, action, resource):
            return PolicyDecisionResult(
                decision=PolicyDecision.DENY,
                reason=f"User lacks permission: {resource}.{action}"
            )
        
        # Check ABAC if mission is involved
        if mission and not self.check_mission_access(user, mission):
            return PolicyDecisionResult(
                decision=PolicyDecision.DENY,
                reason="User does not have access to this mission"
            )
        
        # Evaluate policy engine
        return self.policy_engine.evaluate(policy_context)
    
    def require_approval(self, risk_level: RiskLevel, user: User) -> bool:
        """Check if action requires approval based on risk level."""
        # High and critical risk always require approval
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            return True
        
        # Non-admin users require approval for medium risk
        if risk_level == RiskLevel.MEDIUM:
            if UserRole.ADMIN.value not in user.roles:
                return True
        
        return False


# Predefined roles with permissions
DEFAULT_ROLES = {
    UserRole.VIEWER.value: Role(
        id="viewer",
        name=UserRole.VIEWER,
        description="Can view missions and data",
        permissions=[
            "mission.read",
            "source.read",
            "model.read",
            "evidence.read",
            "audit.read",
        ]
    ),
    UserRole.ANALYST.value: Role(
        id="analyst",
        name=UserRole.ANALYST,
        description="Can analyze data and run inference",
        permissions=[
            "mission.read",
            "mission.create",
            "source.read",
            "model.read",
            "model.infer",
            "evidence.read",
            "evidence.capture",
            "audit.read",
        ]
    ),
    UserRole.OPERATOR.value: Role(
        id="operator",
        name=UserRole.OPERATOR,
        description="Can execute missions and manage sources",
        permissions=[
            "mission.read",
            "mission.create",
            "mission.execute",
            "source.read",
            "source.enable",
            "model.read",
            "model.infer",
            "evidence.read",
            "evidence.capture",
            "evidence.verify",
            "audit.read",
            "orbit.read",
            "orbit.plan",
            "acquisition.plan",
        ]
    ),
    UserRole.MISSION_MANAGER.value: Role(
        id="mission_manager",
        name=UserRole.MISSION_MANAGER,
        description="Can manage missions and approve actions",
        permissions=[
            "mission.read",
            "mission.create",
            "mission.execute",
            "mission.approve",
            "source.read",
            "source.enable",
            "model.read",
            "model.infer",
            "evidence.read",
            "evidence.capture",
            "evidence.verify",
            "audit.read",
            "orbit.read",
            "orbit.plan",
            "acquisition.plan",
            "acquisition.approve",
        ]
    ),
    UserRole.SCIENTIST.value: Role(
        id="scientist",
        name=UserRole.SCIENTIST,
        description="Can manage models and research",
        permissions=[
            "mission.read",
            "source.read",
            "model.read",
            "model.infer",
            "model.manage",
            "evidence.read",
            "evidence.capture",
            "evidence.verify",
            "audit.read",
        ]
    ),
    UserRole.AUDITOR.value: Role(
        id="auditor",
        name=UserRole.AUDITOR,
        description="Can audit system and view logs",
        permissions=[
            "mission.read",
            "source.read",
            "model.read",
            "evidence.read",
            "audit.read",
        ]
    ),
    UserRole.ADMIN.value: Role(
        id="admin",
        name=UserRole.ADMIN,
        description="Full system access",
        permissions=[
            "mission.read",
            "mission.create",
            "mission.execute",
            "mission.approve",
            "source.read",
            "source.enable",
            "model.read",
            "model.infer",
            "model.manage",
            "evidence.read",
            "evidence.capture",
            "evidence.verify",
            "audit.read",
            "orbit.read",
            "orbit.plan",
            "acquisition.plan",
            "acquisition.approve",
            "users.read",
            "users.manage",
            "system.configure",
        ]
    ),
}


def create_default_policy_engine() -> PolicyEngine:
    """Create a policy engine with default roles."""
    return PolicyEngine(DEFAULT_ROLES)
