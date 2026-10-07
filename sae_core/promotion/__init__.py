"""
SAE Promotion Engine.

This module provides a complete Promotion Algorithmic Engine for managing
promotions, campaigns, eligibility, ranking, budget, pacing, attribution,
and analytics.

The Promotion Engine is separate from the GEOINT/Scientific components
and uses common services (IAM, Policy, Audit, Events, Persistence).
"""

from .models import (
    Campaign, Promotion, PromotionCreative, Placement, AudienceRule,
    EligibilityResult, Candidate, Score, RankingResult, Impression,
    Interaction, Conversion, Attribution, Reward, LedgerEntry, Budget,
    PacingState, FrequencyCap, Experiment, FraudSignal, PromotionDecision,
    CampaignStatus, PromotionStatus, PromotionType, InteractionType,
    ConversionStatus, RewardStatus, FraudSignalStatus, ExperimentStatus,
    DecisionType,
)
from .engine import (
    EligibilityEngine, CandidateGenerator, ContextEngine, RankingEngine,
    FrequencyController, BudgetEngine, PacingEngine, AttributionEngine,
    PromotionService,
)
from .api import router as promotion_router

__all__ = [
    # Models
    "Campaign",
    "Promotion",
    "PromotionCreative",
    "Placement",
    "AudienceRule",
    "EligibilityResult",
    "Candidate",
    "Score",
    "RankingResult",
    "Impression",
    "Interaction",
    "Conversion",
    "Attribution",
    "Reward",
    "LedgerEntry",
    "Budget",
    "PacingState",
    "FrequencyCap",
    "Experiment",
    "FraudSignal",
    "PromotionDecision",
    # Enums
    "CampaignStatus",
    "PromotionStatus",
    "PromotionType",
    "InteractionType",
    "ConversionStatus",
    "RewardStatus",
    "FraudSignalStatus",
    "ExperimentStatus",
    "DecisionType",
    # Engines
    "EligibilityEngine",
    "CandidateGenerator",
    "ContextEngine",
    "RankingEngine",
    "FrequencyController",
    "BudgetEngine",
    "PacingEngine",
    "AttributionEngine",
    "PromotionService",
    # API
    "promotion_router",
]
