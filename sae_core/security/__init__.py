"""SAE Core Security Module."""

from .contracts import (
    User,
    Session,
    Permission,
    Role,
    PolicyContext,
    PolicyDecisionResult,
    PolicyEngine,
    Approval,
    ApprovalEngine,
    AuditEvent,
    AuditEngine,
)
from .authentication import (
    AuthenticationService,
    create_user,
)
from .authorization import (
    AuthorizationService,
    DEFAULT_ROLES,
    create_default_policy_engine,
)

__all__ = [
    # Contracts
    "User",
    "Session",
    "Permission",
    "Role",
    "PolicyContext",
    "PolicyDecisionResult",
    "PolicyEngine",
    "Approval",
    "ApprovalEngine",
    "AuditEvent",
    "AuditEngine",
    # Authentication
    "AuthenticationService",
    "create_user",
    # Authorization
    "AuthorizationService",
    "DEFAULT_ROLES",
    "create_default_policy_engine",
]
