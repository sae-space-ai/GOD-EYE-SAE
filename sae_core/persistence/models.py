"""
SAE Core Persistence - SQLAlchemy models.

This module defines database models for all persistent entities.
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    roles = Column(JSON, nullable=False, default=list)
    organization = Column(String, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata_ = Column("metadata", JSON, default=dict)
    
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    missions = relationship("Mission", back_populates="creator")


class Session(Base):
    """User session model."""
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata_ = Column("metadata", JSON, default=dict)
    
    user = relationship("User", back_populates="sessions")
    
    __table_args__ = (
        Index("idx_sessions_expires", "expires_at"),
    )


class Mission(Base):
    """Mission model."""
    __tablename__ = "missions"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    objective = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    area_of_interest = Column(JSON, nullable=False)
    time_window = Column(JSON, nullable=False)
    priority = Column(Integer, nullable=False)
    requested_products = Column(JSON, nullable=False, default=list)
    required_sources = Column(JSON, nullable=False, default=list)
    required_models = Column(JSON, nullable=False, default=list)
    constraints = Column(JSON, default=dict)
    risk_level = Column(String, nullable=False)
    approval_policy = Column(String, nullable=False)
    status = Column(String, nullable=False, index=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata_ = Column("metadata", JSON, default=dict)
    
    creator = relationship("User", back_populates="missions")
    execution_nodes = relationship("ExecutionNode", back_populates="mission", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="mission", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="mission")
    evidence = relationship("Evidence", back_populates="mission", cascade="all, delete-orphan")


class ExecutionNode(Base):
    """Execution node model."""
    __tablename__ = "execution_nodes"
    
    id = Column(String, primary_key=True)
    mission_id = Column(String, ForeignKey("missions.id"), nullable=False, index=True)
    type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    dependencies = Column(JSON, default=list)
    inputs = Column(JSON, default=dict)
    outputs = Column(JSON, default=dict)
    status = Column(String, nullable=False, index=True)
    risk_level = Column(String, nullable=False)
    requires_approval = Column(Boolean, default=False)
    retry_policy = Column(JSON, default=dict)
    timeout = Column(Integer, default=300)
    metadata_ = Column("metadata", JSON, default=dict)
    
    mission = relationship("Mission", back_populates="execution_nodes")


class Approval(Base):
    """Approval model."""
    __tablename__ = "approvals"
    
    id = Column(String, primary_key=True)
    mission_id = Column(String, ForeignKey("missions.id"), nullable=False, index=True)
    execution_node_id = Column(String, nullable=True)
    requested_by = Column(String, nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow)
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    decision = Column(String, nullable=False, index=True)
    reason = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)
    
    mission = relationship("Mission", back_populates="approvals")


class AuditEvent(Base):
    """Audit event model."""
    __tablename__ = "audit_events"
    
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    actor = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False, index=True)
    resource = Column(String, nullable=False)
    resource_id = Column(String, nullable=True)
    mission_id = Column(String, ForeignKey("missions.id"), nullable=True, index=True)
    status = Column(String, nullable=False)
    metadata_ = Column("metadata", JSON, default=dict)
    
    mission = relationship("Mission", back_populates="audit_events")
    
    __table_args__ = (
        Index("idx_audit_timestamp", "timestamp"),
        Index("idx_audit_actor_action", "actor", "action"),
    )


class Evidence(Base):
    """Evidence model."""
    __tablename__ = "evidence"
    
    id = Column(String, primary_key=True)
    mission_id = Column(String, ForeignKey("missions.id"), nullable=False, index=True)
    source_id = Column(String, nullable=False, index=True)
    entity_id = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    captured_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    source_timestamp = Column(DateTime, nullable=False)
    coordinates = Column(JSON, nullable=False)
    geometry = Column(JSON, nullable=True)
    source_url = Column(String, nullable=True)
    source_type = Column(String, nullable=False)
    metadata_ = Column("metadata", JSON, default=dict)
    confidence = Column(Float, nullable=True)
    status = Column(String, nullable=False, index=True)
    hash = Column(String, nullable=False)
    snapshot = Column(Text, nullable=False)
    provenance = Column(JSON, nullable=False)
    
    mission = relationship("Mission", back_populates="evidence")


class Model(Base):
    """AI model registry model."""
    __tablename__ = "models"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    version = Column(String, nullable=False)
    model_type = Column(String, nullable=False)
    modalities = Column(JSON, nullable=False, default=list)
    input_contract = Column(JSON, nullable=False)
    output_contract = Column(JSON, nullable=False)
    status = Column(String, nullable=False, index=True)
    device = Column(String, nullable=False)
    precision = Column(String, nullable=False)
    frozen = Column(Boolean, default=False)
    checkpoint = Column(String, nullable=True)
    capabilities = Column(JSON, default=list)
    metadata_ = Column("metadata", JSON, default=dict)


class Source(Base):
    """Data source registry model."""
    __tablename__ = "sources"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False, index=True)
    provider = Column(String, nullable=False)
    status = Column(String, nullable=False, index=True)
    configured = Column(Boolean, default=False)
    requires_auth = Column(Boolean, default=False)
    requires_server = Column(Boolean, default=False)
    last_fetch = Column(DateTime, nullable=True)
    last_success = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    refresh_interval = Column(Integer, nullable=True)
    provenance = Column(String, nullable=False)
    capabilities = Column(JSON, default=list)
    metadata_ = Column("metadata", JSON, default=dict)


class Event(Base):
    """Event model."""
    __tablename__ = "events"
    
    id = Column(String, primary_key=True)
    event_type = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    producer = Column(String, nullable=False)
    mission_id = Column(String, nullable=True, index=True)
    correlation_id = Column(String, nullable=False, index=True)
    causation_id = Column(String, nullable=True)
    payload = Column(JSON, nullable=False)
    metadata_ = Column("metadata", JSON, default=dict)
    
    __table_args__ = (
        Index("idx_events_timestamp", "timestamp"),
        Index("idx_events_correlation", "correlation_id"),
    )
