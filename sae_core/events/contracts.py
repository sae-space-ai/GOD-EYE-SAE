"""
SAE Core Events - Event bus and event contracts.

This module defines the event system for asynchronous communication
and correlation tracking.
"""

from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from dataclasses import dataclass, field
from ..common.enums import EventType, generate_id, utc_now


# ============================================================================
# EVENT
# ============================================================================

@dataclass
class Event:
    """System event."""
    id: str
    event_type: EventType
    timestamp: datetime
    producer: str  # Component that produced event
    mission_id: Optional[str] = None
    correlation_id: str = field(default_factory=generate_id)
    causation_id: Optional[str] = None  # Event that caused this event
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# EVENT BUS
# ============================================================================

class EventBus:
    """
    Event bus for asynchronous communication.
    
    Supports:
    - Publish/subscribe pattern
    - Correlation ID propagation
    - Event filtering by type
    """
    
    def __init__(self):
        """Initialize event bus."""
        self.subscribers: Dict[EventType, List[Callable[[Event], None]]] = {}
        self.events: List[Event] = []
    
    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """Subscribe to event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
    
    def publish(self, event: Event) -> None:
        """Publish event to subscribers."""
        self.events.append(event)
        
        # Notify subscribers
        if event.event_type in self.subscribers:
            for handler in self.subscribers[event.event_type]:
                try:
                    handler(event)
                except Exception as e:
                    # Log error but don't fail
                    pass
    
    def create_event(
        self,
        event_type: EventType,
        producer: str,
        payload: Dict[str, Any],
        mission_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None
    ) -> Event:
        """Create and publish event."""
        event = Event(
            id=generate_id(),
            event_type=event_type,
            timestamp=utc_now(),
            producer=producer,
            mission_id=mission_id,
            correlation_id=correlation_id or generate_id(),
            causation_id=causation_id,
            payload=payload
        )
        self.publish(event)
        return event
    
    def get_events(self, mission_id: Optional[str] = None, limit: int = 100) -> List[Event]:
        """Get events, optionally filtered by mission."""
        if mission_id:
            events = [e for e in self.events if e.mission_id == mission_id]
        else:
            events = self.events
        
        return events[-limit:]


# ============================================================================
# CORRELATION TRACKER
# ============================================================================

class CorrelationTracker:
    """
    Tracks correlation IDs across operations.
    
    Ensures all related operations share the same correlation ID:
    user request → mission → plan → source → inference → prediction → evidence → approval → execution
    """
    
    def __init__(self):
        """Initialize correlation tracker."""
        self.current_correlation_id: Optional[str] = None
    
    def start_correlation(self, correlation_id: Optional[str] = None) -> str:
        """Start new correlation."""
        self.current_correlation_id = correlation_id or generate_id()
        return self.current_correlation_id
    
    def get_correlation_id(self) -> Optional[str]:
        """Get current correlation ID."""
        return self.current_correlation_id
    
    def end_correlation(self) -> None:
        """End current correlation."""
        self.current_correlation_id = None
