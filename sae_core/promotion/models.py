"""
SAE Promotion Engine - Domain Models.

This module defines all domain models for the Promotion Algorithmic Engine.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class CampaignStatus(str, Enum):
    """Campaign lifecycle states."""
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PromotionStatus(str, Enum):
    """Promotion lifecycle states."""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PromotionType(str, Enum):
    """Types of promotions."""
    SPONSORED = "SPONSORED"
    FEATURED = "FEATURED"
    RECOMMENDED = "RECOMMENDED"


class InteractionType(str, Enum):
    """Types of user interactions."""
    VIEW = "VIEW"
    CLICK = "CLICK"
    OPEN = "OPEN"
    ENGAGEMENT = "ENGAGEMENT"


class ConversionStatus(str, Enum):
    """Conversion states."""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REVERSED = "REVERSED"


class RewardStatus(str, Enum):
    """Reward states."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    CANCELLED = "CANCELLED"
    PAID_OR_REDEEMED = "PAID_OR_REDEEMED"


class FraudSignalStatus(str, Enum):
    """Fraud signal states."""
    SIGNAL = "SIGNAL"
    UNDER_REVIEW = "UNDER_REVIEW"
    CONFIRMED = "CONFIRMED"
    DISMISSED = "DISMISSED"


class ExperimentStatus(str, Enum):
    """Experiment states."""
    DRAFT = "DRAFT"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class DecisionType(str, Enum):
    """Decision classification."""
    EDITORIAL = "EDITORIAL"
    ORGANIC_RECOMMENDATION = "ORGANIC_RECOMMENDATION"
    SPONSORED_PROMOTION = "SPONSORED_PROMOTION"


# ============================================================================
# DOMAIN MODELS
# ============================================================================

@dataclass
class Campaign:
    """Campaign model."""
    id: str
    name: str
    status: CampaignStatus
    advertiser_or_owner: str
    objective: str
    start_at: datetime
    end_at: datetime
    budget: Decimal
    daily_budget: Optional[Decimal] = None
    priority: int = 5
    targeting_rules: Dict[str, Any] = field(default_factory=dict)
    frequency_cap: Optional[int] = None
    placements: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_active(self, at: Optional[datetime] = None) -> bool:
        """Check if campaign is active at given time."""
        check_time = at or datetime.utcnow()
        return (
            self.status == CampaignStatus.ACTIVE and
            self.start_at <= check_time <= self.end_at
        )


@dataclass
class Promotion:
    """Promotion model."""
    id: str
    campaign_id: str
    title: str
    description: str
    creative_reference: str
    destination: str
    placement: str
    status: PromotionStatus
    promotion_type: PromotionType = PromotionType.SPONSORED
    priority: int = 5
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PromotionCreative:
    """Promotion creative assets."""
    id: str
    promotion_id: str
    asset_type: str  # "image", "video", "text"
    asset_url: str
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None  # for video
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Placement:
    """Placement definition."""
    id: str
    name: str
    description: str
    format: str  # "banner", "native", "video", etc.
    dimensions: Optional[Dict[str, int]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AudienceRule:
    """Audience targeting rule."""
    id: str
    campaign_id: str
    rule_type: str  # "demographic", "behavioral", "geographic", etc.
    conditions: Dict[str, Any]
    exclude: bool = False


@dataclass
class EligibilityResult:
    """Result of eligibility check."""
    promotion_id: str
    eligible: bool
    reason_codes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Candidate:
    """Promotion candidate for ranking."""
    promotion: Promotion
    campaign: Campaign
    eligibility: EligibilityResult
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Score:
    """Score component."""
    name: str
    value: float
    weight: float
    weighted_value: float


@dataclass
class RankingResult:
    """Result of ranking."""
    candidate: Candidate
    total_score: float
    score_components: List[Score]
    position: int
    policy_filters: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    algorithm_version: str = "1.0.0"


@dataclass
class Impression:
    """Impression record."""
    id: str
    promotion_id: str
    campaign_id: str
    placement: str
    timestamp: datetime
    session_reference: str
    context_reference: str
    decision_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Interaction:
    """Interaction record."""
    id: str
    impression_id: str
    promotion_id: str
    campaign_id: str
    interaction_type: InteractionType
    timestamp: datetime
    session_reference: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Conversion:
    """Conversion record."""
    id: str
    campaign_id: str
    promotion_id: str
    event_type: str
    value: Decimal
    currency: str
    timestamp: datetime
    reference: str
    status: ConversionStatus = ConversionStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Attribution:
    """Attribution record."""
    id: str
    conversion_id: str
    campaign_id: str
    promotion_id: str
    interaction_id: Optional[str] = None
    attribution_model: str  # "last_interaction", "first_interaction", etc.
    attributed_value: Decimal
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Reward:
    """Reward record."""
    id: str
    user_reference: str
    conversion_id: str
    reward_type: str  # "points", "discount", "cashback", etc.
    amount: Decimal
    currency_or_unit: str
    status: RewardStatus = RewardStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LedgerEntry:
    """Ledger entry for rewards."""
    id: str
    account: str
    entry_type: str  # "credit", "debit"
    amount: Decimal
    reference: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    balance_effect: Decimal = Decimal("0")
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Budget:
    """Budget tracking."""
    campaign_id: str
    total_budget: Decimal
    daily_budget: Optional[Decimal] = None
    spent: Decimal = Decimal("0")
    reserved: Decimal = Decimal("0")
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def remaining(self) -> Decimal:
        """Calculate remaining budget."""
        return self.total_budget - self.spent - self.reserved
    
    def can_serve(self, amount: Decimal) -> bool:
        """Check if budget can serve this amount."""
        return self.remaining >= amount


@dataclass
class PacingState:
    """Pacing state for campaign."""
    campaign_id: str
    target_spend_rate: Decimal  # per hour
    current_spend_rate: Decimal
    last_updated: datetime = field(default_factory=datetime.utcnow)
    adjustment_factor: float = 1.0


@dataclass
class FrequencyCap:
    """Frequency cap configuration."""
    id: str
    campaign_id: Optional[str] = None
    promotion_id: Optional[str] = None
    placement: Optional[str] = None
    max_impressions: int
    time_window_seconds: int
    scope: str = "user"  # "user", "session", "device"


@dataclass
class Experiment:
    """A/B test experiment."""
    id: str
    name: str
    variants: List[Dict[str, Any]]
    allocation: Dict[str, float]  # variant_id -> percentage
    start_at: datetime
    end_at: datetime
    metrics: List[str]
    status: ExperimentStatus = ExperimentStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FraudSignal:
    """Fraud detection signal."""
    id: str
    signal_type: str  # "duplicate_conversion", "rapid_clicks", etc.
    promotion_id: Optional[str] = None
    campaign_id: Optional[str] = None
    user_reference: Optional[str] = None
    session_reference: Optional[str] = None
    confidence: float
    status: FraudSignalStatus = FraudSignalStatus.SIGNAL
    detected_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PromotionDecision:
    """Final promotion decision with explainability."""
    id: str
    decision_type: DecisionType
    selected_promotion: Optional[Promotion] = None
    all_candidates: List[Candidate] = field(default_factory=list)
    ranking_results: List[RankingResult] = field(default_factory=list)
    filtered_out: List[Dict[str, Any]] = field(default_factory=list)
    policy_filters_applied: List[str] = field(default_factory=list)
    frequency_caps_applied: List[str] = field(default_factory=list)
    budget_status: Optional[Dict[str, Any]] = None
    algorithm_id: str = "sae-promotion-engine"
    algorithm_version: str = "1.0.0"
    configuration_version: str = "1.0.0"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
