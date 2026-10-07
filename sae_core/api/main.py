"""
SAE Core API - FastAPI application.

This module implements the HTTP API for SAE Core using FastAPI.
"""

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import logging

from ..config.settings import get_config
from ..persistence import get_session, init_db
from ..persistence.repositories import (
    UserRepository,
    SessionRepository,
    MissionRepository,
    ApprovalRepository,
    AuditRepository,
    EvidenceRepository,
    ModelRepository,
    SourceRepository,
)
from ..security.authentication import AuthenticationService
from ..security.authorization import AuthorizationService, create_default_policy_engine
from ..security.contracts import PolicyEngine
from ..common.enums import generate_id, utc_now, UserRole
from ..persistence.models import User as UserModel, Session as SessionModel

# Configure logging
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SAE Intelligence Core API",
    description="API for GOD EYE SAE Intelligence Core",
    version="1.0.0"
)

# CORS middleware
config = get_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()


# Dependency: Database session
def get_db():
    """Get database session."""
    with get_session() as session:
        yield session


# Dependency: Current user
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> UserModel:
    """Get current authenticated user."""
    token = credentials.credentials
    session_repo = SessionRepository(db)
    user_repo = UserRepository(db)
    
    auth_service = AuthenticationService(user_repo, session_repo)
    user = auth_service.validate_session(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return user


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()
    logger.info("SAE Core API started")


# ============================================================================
# SYSTEM ENDPOINTS
# ============================================================================

@app.get("/api/v1/system/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "sae-core",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": config.environment
    }


# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@app.post("/api/v1/auth/login")
async def login(
    username: str,
    password: str,
    db: Session = Depends(get_db)
):
    """Login and get access token."""
    user_repo = UserRepository(db)
    session_repo = SessionRepository(db)
    
    auth_service = AuthenticationService(user_repo, session_repo)
    user = auth_service.authenticate_user(username, password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    session = auth_service.create_session(user)
    
    return {
        "access_token": session.token,
        "refresh_token": session.metadata_.get("refresh_token"),
        "token_type": "bearer",
        "expires_at": session.expires_at.isoformat(),
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "roles": user.roles
        }
    }


@app.post("/api/v1/auth/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Logout and invalidate session."""
    token = credentials.credentials
    session_repo = SessionRepository(db)
    user_repo = UserRepository(db)
    
    auth_service = AuthenticationService(user_repo, session_repo)
    auth_service.logout(token)
    
    return {"status": "logged_out"}


@app.get("/api/v1/auth/me")
async def get_current_user_info(
    current_user: UserModel = Depends(get_current_user)
):
    """Get current user information."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "roles": current_user.roles,
        "organization": current_user.organization,
        "created_at": current_user.created_at.isoformat()
    }


# ============================================================================
# USERS ENDPOINTS
# ============================================================================

@app.get("/api/v1/users")
async def list_users(
    limit: int = 100,
    offset: int = 0,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all users (admin only)."""
    if UserRole.ADMIN.value not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    user_repo = UserRepository(db)
    users = user_repo.list_all(limit=limit, offset=offset)
    
    return {
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "roles": user.roles,
                "organization": user.organization,
                "active": user.active,
                "created_at": user.created_at.isoformat()
            }
            for user in users
        ],
        "total": len(users)
    }


# ============================================================================
# MISSIONS ENDPOINTS
# ============================================================================

@app.get("/api/v1/missions")
async def list_missions(
    status: Optional[str] = None,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List missions."""
    mission_repo = MissionRepository(db)
    
    if status:
        missions = mission_repo.list_by_status(status, limit=limit)
    else:
        missions = mission_repo.list_by_user(current_user.id, limit=limit)
    
    return {
        "missions": [
            {
                "id": mission.id,
                "name": mission.name,
                "objective": mission.objective,
                "status": mission.status,
                "priority": mission.priority,
                "risk_level": mission.risk_level,
                "created_by": mission.created_by,
                "created_at": mission.created_at.isoformat(),
                "updated_at": mission.updated_at.isoformat()
            }
            for mission in missions
        ],
        "total": len(missions)
    }


@app.get("/api/v1/missions/{mission_id}")
async def get_mission(
    mission_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get mission by ID."""
    mission_repo = MissionRepository(db)
    mission = mission_repo.get_by_id(mission_id)
    
    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mission not found"
        )
    
    return {
        "id": mission.id,
        "name": mission.name,
        "objective": mission.objective,
        "description": mission.description,
        "area_of_interest": mission.area_of_interest,
        "time_window": mission.time_window,
        "priority": mission.priority,
        "requested_products": mission.requested_products,
        "required_sources": mission.required_sources,
        "required_models": mission.required_models,
        "constraints": mission.constraints,
        "risk_level": mission.risk_level,
        "approval_policy": mission.approval_policy,
        "status": mission.status,
        "created_by": mission.created_by,
        "created_at": mission.created_at.isoformat(),
        "updated_at": mission.updated_at.isoformat()
    }


@app.post("/api/v1/missions/{mission_id}/execute")
async def execute_mission(
    mission_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a mission."""
    # Check permission
    policy_engine = create_default_policy_engine()
    auth_service = AuthorizationService(policy_engine)
    
    decision = auth_service.evaluate_policy(
        user=current_user,
        action="execute",
        resource="mission",
        resource_id=mission_id
    )
    
    if decision.decision.value == "DENY":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=decision.reason
        )
    
    # TODO: Implement actual mission execution
    return {
        "status": "execution_started",
        "mission_id": mission_id,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# SOURCES ENDPOINTS
# ============================================================================

@app.get("/api/v1/sources")
async def list_sources(
    category: Optional[str] = None,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List data sources."""
    source_repo = SourceRepository(db)
    
    if category:
        sources = source_repo.list_by_category(category)
    else:
        sources = source_repo.list_all() if hasattr(source_repo, 'list_all') else []
    
    return {
        "sources": [
            {
                "id": source.id,
                "name": source.name,
                "category": source.category,
                "provider": source.provider,
                "status": source.status,
                "configured": source.configured,
                "last_fetch": source.last_fetch.isoformat() if source.last_fetch else None,
                "last_success": source.last_success.isoformat() if source.last_success else None
            }
            for source in sources
        ],
        "total": len(sources)
    }


# ============================================================================
# MODELS ENDPOINTS
# ============================================================================

@app.get("/api/v1/models")
async def list_models(
    status: Optional[str] = None,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List AI models."""
    model_repo = ModelRepository(db)
    
    if status:
        models = model_repo.list_by_status(status)
    else:
        models = model_repo.list_all() if hasattr(model_repo, 'list_all') else []
    
    return {
        "models": [
            {
                "id": model.id,
                "name": model.name,
                "version": model.version,
                "model_type": model.model_type,
                "modalities": model.modalities,
                "status": model.status,
                "device": model.device,
                "precision": model.precision
            }
            for model in models
        ],
        "total": len(models)
    }


# ============================================================================
# EVIDENCE ENDPOINTS
# ============================================================================

@app.get("/api/v1/evidence")
async def list_evidence(
    mission_id: Optional[str] = None,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List evidence."""
    evidence_repo = EvidenceRepository(db)
    
    if mission_id:
        evidence_list = evidence_repo.list_by_mission(mission_id)
    else:
        evidence_list = []
    
    return {
        "evidence": [
            {
                "id": evidence.id,
                "mission_id": evidence.mission_id,
                "source_id": evidence.source_id,
                "entity_type": evidence.entity_type,
                "captured_at": evidence.captured_at.isoformat(),
                "status": evidence.status,
                "hash": evidence.hash
            }
            for evidence in evidence_list[:limit]
        ],
        "total": len(evidence_list)
    }


# ============================================================================
# APPROVALS ENDPOINTS
# ============================================================================

@app.get("/api/v1/approvals")
async def list_approvals(
    mission_id: Optional[str] = None,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List approvals."""
    approval_repo = ApprovalRepository(db)
    
    if mission_id:
        approvals = approval_repo.list_by_mission(mission_id)
    else:
        approvals = approval_repo.list_pending()
    
    return {
        "approvals": [
            {
                "id": approval.id,
                "mission_id": approval.mission_id,
                "execution_node_id": approval.execution_node_id,
                "requested_by": approval.requested_by,
                "requested_at": approval.requested_at.isoformat(),
                "reviewed_by": approval.reviewed_by,
                "reviewed_at": approval.reviewed_at.isoformat() if approval.reviewed_at else None,
                "decision": approval.decision,
                "reason": approval.reason
            }
            for approval in approvals
        ],
        "total": len(approvals)
    }


# ============================================================================
# AUDIT ENDPOINTS
# ============================================================================

@app.get("/api/v1/audit")
async def list_audit_events(
    mission_id: Optional[str] = None,
    actor: Optional[str] = None,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List audit events."""
    audit_repo = AuditRepository(db)
    
    if mission_id:
        events = audit_repo.list_by_mission(mission_id, limit=limit)
    elif actor:
        events = audit_repo.list_by_actor(actor, limit=limit)
    else:
        events = []
    
    return {
        "events": [
            {
                "id": event.id,
                "timestamp": event.timestamp.isoformat(),
                "actor": event.actor,
                "action": event.action,
                "resource": event.resource,
                "resource_id": event.resource_id,
                "mission_id": event.mission_id,
                "status": event.status
            }
            for event in events
        ],
        "total": len(events)
    }
