"""
SAE Core Persistence - Repository interfaces and implementations.

This module provides repository pattern implementations for all persistent entities.
"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from .models import (
    User as UserModel,
    Session as SessionModel,
    Mission as MissionModel,
    ExecutionNode as ExecutionNodeModel,
    Approval as ApprovalModel,
    AuditEvent as AuditEventModel,
    Evidence as EvidenceModel,
    Model as ModelModel,
    Source as SourceModel,
    Event as EventModel,
)


class UserRepository:
    """Repository for User entities."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, user: UserModel) -> UserModel:
        """Create a new user."""
        self.session.add(user)
        self.session.flush()
        return user
    
    def get_by_id(self, user_id: str) -> Optional[UserModel]:
        """Get user by ID."""
        return self.session.query(UserModel).filter(UserModel.id == user_id).first()
    
    def get_by_username(self, username: str) -> Optional[UserModel]:
        """Get user by username."""
        return self.session.query(UserModel).filter(UserModel.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[UserModel]:
        """Get user by email."""
        return self.session.query(UserModel).filter(UserModel.email == email).first()
    
    def list_all(self, limit: int = 100, offset: int = 0) -> List[UserModel]:
        """List all users."""
        return self.session.query(UserModel).offset(offset).limit(limit).all()
    
    def update(self, user: UserModel) -> UserModel:
        """Update user."""
        self.session.flush()
        return user
    
    def delete(self, user_id: str) -> bool:
        """Delete user."""
        user = self.get_by_id(user_id)
        if user:
            self.session.delete(user)
            return True
        return False


class SessionRepository:
    """Repository for Session entities."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, session_obj: SessionModel) -> SessionModel:
        """Create a new session."""
        self.session.add(session_obj)
        self.session.flush()
        return session_obj
    
    def get_by_token(self, token: str) -> Optional[SessionModel]:
        """Get session by token."""
        return self.session.query(SessionModel).filter(SessionModel.token == token).first()
    
    def get_by_user_id(self, user_id: str) -> List[SessionModel]:
        """Get all sessions for a user."""
        return self.session.query(SessionModel).filter(SessionModel.user_id == user_id).all()
    
    def delete_expired(self) -> int:
        """Delete expired sessions."""
        now = datetime.utcnow()
        count = self.session.query(SessionModel).filter(SessionModel.expires_at < now).delete()
        return count
    
    def delete_by_token(self, token: str) -> bool:
        """Delete session by token."""
        session_obj = self.get_by_token(token)
        if session_obj:
            self.session.delete(session_obj)
            return True
        return False


class MissionRepository:
    """Repository for Mission entities."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, mission: MissionModel) -> MissionModel:
        """Create a new mission."""
        self.session.add(mission)
        self.session.flush()
        return mission
    
    def get_by_id(self, mission_id: str) -> Optional[MissionModel]:
        """Get mission by ID."""
        return self.session.query(MissionModel).filter(MissionModel.id == mission_id).first()
    
    def list_by_status(self, status: str, limit: int = 100) -> List[MissionModel]:
        """List missions by status."""
        return self.session.query(MissionModel).filter(MissionModel.status == status).limit(limit).all()
    
    def list_by_user(self, user_id: str, limit: int = 100) -> List[MissionModel]:
        """List missions by user."""
        return self.session.query(MissionModel).filter(MissionModel.created_by == user_id).limit(limit).all()
    
    def update(self, mission: MissionModel) -> MissionModel:
        """Update mission."""
        mission.updated_at = datetime.utcnow()
        self.session.flush()
        return mission
    
    def delete(self, mission_id: str) -> bool:
        """Delete mission."""
        mission = self.get_by_id(mission_id)
        if mission:
            self.session.delete(mission)
            return True
        return False


class ApprovalRepository:
    """Repository for Approval entities."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, approval: ApprovalModel) -> ApprovalModel:
        """Create a new approval."""
        self.session.add(approval)
        self.session.flush()
        return approval
    
    def get_by_id(self, approval_id: str) -> Optional[ApprovalModel]:
        """Get approval by ID."""
        return self.session.query(ApprovalModel).filter(ApprovalModel.id == approval_id).first()
    
    def list_by_mission(self, mission_id: str) -> List[ApprovalModel]:
        """List approvals by mission."""
        return self.session.query(ApprovalModel).filter(ApprovalModel.mission_id == mission_id).all()
    
    def list_pending(self) -> List[ApprovalModel]:
        """List pending approvals."""
        return self.session.query(ApprovalModel).filter(ApprovalModel.decision == "PENDING").all()
    
    def update(self, approval: ApprovalModel) -> ApprovalModel:
        """Update approval."""
        self.session.flush()
        return approval


class AuditRepository:
    """Repository for AuditEvent entities."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, event: AuditEventModel) -> AuditEventModel:
        """Create a new audit event."""
        self.session.add(event)
        self.session.flush()
        return event
    
    def get_by_id(self, event_id: str) -> Optional[AuditEventModel]:
        """Get audit event by ID."""
        return self.session.query(AuditEventModel).filter(AuditEventModel.id == event_id).first()
    
    def list_by_mission(self, mission_id: str, limit: int = 100) -> List[AuditEventModel]:
        """List audit events by mission."""
        return (
            self.session.query(AuditEventModel)
            .filter(AuditEventModel.mission_id == mission_id)
            .order_by(AuditEventModel.timestamp.desc())
            .limit(limit)
            .all()
        )
    
    def list_by_actor(self, actor: str, limit: int = 100) -> List[AuditEventModel]:
        """List audit events by actor."""
        return (
            self.session.query(AuditEventModel)
            .filter(AuditEventModel.actor == actor)
            .order_by(AuditEventModel.timestamp.desc())
            .limit(limit)
            .all()
        )
    
    def list_by_time_range(self, start: datetime, end: datetime, limit: int = 100) -> List[AuditEventModel]:
        """List audit events by time range."""
        return (
            self.session.query(AuditEventModel)
            .filter(AuditEventModel.timestamp >= start, AuditEventModel.timestamp <= end)
            .order_by(AuditEventModel.timestamp.desc())
            .limit(limit)
            .all()
        )


class EvidenceRepository:
    """Repository for Evidence entities."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, evidence: EvidenceModel) -> EvidenceModel:
        """Create a new evidence."""
        self.session.add(evidence)
        self.session.flush()
        return evidence
    
    def get_by_id(self, evidence_id: str) -> Optional[EvidenceModel]:
        """Get evidence by ID."""
        return self.session.query(EvidenceModel).filter(EvidenceModel.id == evidence_id).first()
    
    def list_by_mission(self, mission_id: str) -> List[EvidenceModel]:
        """List evidence by mission."""
        return self.session.query(EvidenceModel).filter(EvidenceModel.mission_id == mission_id).all()
    
    def list_by_source(self, source_id: str) -> List[EvidenceModel]:
        """List evidence by source."""
        return self.session.query(EvidenceModel).filter(EvidenceModel.source_id == source_id).all()
    
    def update(self, evidence: EvidenceModel) -> EvidenceModel:
        """Update evidence."""
        self.session.flush()
        return evidence


class ModelRepository:
    """Repository for Model entities."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, model: ModelModel) -> ModelModel:
        """Create a new model."""
        self.session.add(model)
        self.session.flush()
        return model
    
    def get_by_id(self, model_id: str) -> Optional[ModelModel]:
        """Get model by ID."""
        return self.session.query(ModelModel).filter(ModelModel.id == model_id).first()
    
    def list_by_status(self, status: str) -> List[ModelModel]:
        """List models by status."""
        return self.session.query(ModelModel).filter(ModelModel.status == status).all()
    
    def update(self, model: ModelModel) -> ModelModel:
        """Update model."""
        self.session.flush()
        return model


class SourceRepository:
    """Repository for Source entities."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, source: SourceModel) -> SourceModel:
        """Create a new source."""
        self.session.add(source)
        self.session.flush()
        return source
    
    def get_by_id(self, source_id: str) -> Optional[SourceModel]:
        """Get source by ID."""
        return self.session.query(SourceModel).filter(SourceModel.id == source_id).first()
    
    def list_by_category(self, category: str) -> List[SourceModel]:
        """List sources by category."""
        return self.session.query(SourceModel).filter(SourceModel.category == category).all()
    
    def list_by_status(self, status: str) -> List[SourceModel]:
        """List sources by status."""
        return self.session.query(SourceModel).filter(SourceModel.status == status).all()
    
    def update(self, source: SourceModel) -> SourceModel:
        """Update source."""
        self.session.flush()
        return source


class EventRepository:
    """Repository for Event entities."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, event: EventModel) -> EventModel:
        """Create a new event."""
        self.session.add(event)
        self.session.flush()
        return event
    
    def get_by_id(self, event_id: str) -> Optional[EventModel]:
        """Get event by ID."""
        return self.session.query(EventModel).filter(EventModel.id == event_id).first()
    
    def list_by_mission(self, mission_id: str, limit: int = 100) -> List[EventModel]:
        """List events by mission."""
        return (
            self.session.query(EventModel)
            .filter(EventModel.mission_id == mission_id)
            .order_by(EventModel.timestamp.desc())
            .limit(limit)
            .all()
        )
    
    def list_by_correlation(self, correlation_id: str) -> List[EventModel]:
        """List events by correlation ID."""
        return (
            self.session.query(EventModel)
            .filter(EventModel.correlation_id == correlation_id)
            .order_by(EventModel.timestamp.asc())
            .all()
        )
