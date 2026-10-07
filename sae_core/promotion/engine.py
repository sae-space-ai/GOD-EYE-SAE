"""
SAE Promotion Engine - Core Components.

This module implements the core algorithmic components of the Promotion Engine.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal
import hashlib

from .models import (
    Campaign, Promotion, Candidate, EligibilityResult, RankingResult, Score,
    Impression, Interaction, Conversion, Attribution, Reward, Budget,
    PacingState, FrequencyCap, PromotionDecision, DecisionType,
    CampaignStatus, PromotionStatus, InteractionType, ConversionStatus,
    RewardStatus,
)


# ============================================================================
# ELIGIBILITY ENGINE
# ============================================================================

class EligibilityEngine:
    """Determines if promotions are eligible for serving."""
    
    def check_eligibility(
        self,
        promotion: Promotion,
        campaign: Campaign,
        context: Dict[str, Any],
        budget: Budget,
        frequency_counts: Dict[str, int]
    ) -> EligibilityResult:
        """
        Check if a promotion is eligible.
        
        Args:
            promotion: Promotion to check
            campaign: Parent campaign
            context: Request context (placement, user, etc.)
            budget: Campaign budget
            frequency_counts: Current frequency counts
        
        Returns:
            EligibilityResult with eligible flag and reason codes
        """
        reason_codes = []
        
        # Check campaign status
        if not campaign.is_active():
            reason_codes.append("CAMPAIGN_INACTIVE")
        
        # Check promotion status
        if promotion.status != PromotionStatus.ACTIVE:
            reason_codes.append("PROMOTION_INACTIVE")
        
        # Check placement
        if promotion.placement not in campaign.placements:
            reason_codes.append("PLACEMENT_MISMATCH")
        
        # Check budget
        if budget.remaining <= Decimal("0"):
            reason_codes.append("BUDGET_EXHAUSTED")
        
        # Check frequency cap
        if campaign.frequency_cap:
            current_count = frequency_counts.get(promotion.id, 0)
            if current_count >= campaign.frequency_cap:
                reason_codes.append("FREQUENCY_CAP_EXCEEDED")
        
        # Check targeting rules (simplified)
        targeting_rules = campaign.targeting_rules
        if targeting_rules:
            # Add targeting logic here
            pass
        
        eligible = len(reason_codes) == 0
        
        return EligibilityResult(
            promotion_id=promotion.id,
            eligible=eligible,
            reason_codes=reason_codes
        )


# ============================================================================
# CANDIDATE GENERATOR
# ============================================================================

class CandidateGenerator:
    """Generates promotion candidates for ranking."""
    
    def generate_candidates(
        self,
        promotions: List[Promotion],
        campaigns: Dict[str, Campaign],
        context: Dict[str, Any]
    ) -> List[Candidate]:
        """
        Generate candidates from promotions.
        
        Args:
            promotions: Available promotions
            campaigns: Campaign lookup
            context: Request context
        
        Returns:
            List of candidates
        """
        candidates = []
        
        for promotion in promotions:
            campaign = campaigns.get(promotion.campaign_id)
            if not campaign:
                continue
            
            # Create candidate (eligibility checked later)
            candidate = Candidate(
                promotion=promotion,
                campaign=campaign,
                eligibility=EligibilityResult(
                    promotion_id=promotion.id,
                    eligible=True  # Will be updated by EligibilityEngine
                ),
                context=context
            )
            candidates.append(candidate)
        
        return candidates


# ============================================================================
# CONTEXT ENGINE
# ============================================================================

class ContextEngine:
    """Builds context for promotion decisions."""
    
    def build_context(
        self,
        placement: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        language: Optional[str] = None,
        device_class: Optional[str] = None,
        content_category: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Build context for promotion decision.
        
        NOTE: Does not use sensitive attributes by default.
        """
        context = {
            "placement": placement,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if user_id:
            context["user_id"] = user_id
        if session_id:
            context["session_id"] = session_id
        if language:
            context["language"] = language
        if device_class:
            context["device_class"] = device_class
        if content_category:
            context["content_category"] = content_category
        
        # Add any additional non-sensitive context
        for key, value in kwargs.items():
            if key not in ["race", "religion", "health", "sexual_orientation", "political_ideology"]:
                context[key] = value
        
        return context


# ============================================================================
# RANKING ENGINE
# ============================================================================

class RankingEngine:
    """Ranks promotion candidates using deterministic scoring."""
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize ranking engine.
        
        Args:
            weights: Scoring weights (relevance, quality, priority, performance, pacing, diversity)
        """
        self.weights = weights or {
            "relevance": 0.3,
            "quality": 0.2,
            "priority": 0.2,
            "performance": 0.15,
            "pacing": 0.1,
            "diversity": 0.05,
        }
    
    def rank(
        self,
        candidates: List[Candidate],
        historical_performance: Dict[str, float],
        pacing_states: Dict[str, PacingState]
    ) -> List[RankingResult]:
        """
        Rank candidates.
        
        Args:
            candidates: Eligible candidates
            historical_performance: Historical performance metrics
            pacing_states: Current pacing states
        
        Returns:
            Ranked list of RankingResult
        """
        ranking_results = []
        
        for idx, candidate in enumerate(candidates):
            # Calculate score components
            scores = self._calculate_scores(
                candidate,
                historical_performance,
                pacing_states
            )
            
            # Calculate total score
            total_score = sum(score.weighted_value for score in scores)
            
            ranking_result = RankingResult(
                candidate=candidate,
                total_score=total_score,
                score_components=scores,
                position=idx + 1,
                algorithm_version="1.0.0"
            )
            ranking_results.append(ranking_result)
        
        # Sort by total score descending
        ranking_results.sort(key=lambda x: x.total_score, reverse=True)
        
        # Update positions
        for idx, result in enumerate(ranking_results):
            result.position = idx + 1
        
        return ranking_results
    
    def _calculate_scores(
        self,
        candidate: Candidate,
        historical_performance: Dict[str, float],
        pacing_states: Dict[str, PacingState]
    ) -> List[Score]:
        """Calculate score components for a candidate."""
        scores = []
        
        # Relevance (simplified)
        relevance = 0.5  # Default, should be calculated based on context
        scores.append(Score(
            name="relevance",
            value=relevance,
            weight=self.weights["relevance"],
            weighted_value=relevance * self.weights["relevance"]
        ))
        
        # Quality (based on promotion priority)
        quality = candidate.promotion.priority / 10.0
        scores.append(Score(
            name="quality",
            value=quality,
            weight=self.weights["quality"],
            weighted_value=quality * self.weights["quality"]
        ))
        
        # Priority (campaign priority)
        priority = candidate.campaign.priority / 10.0
        scores.append(Score(
            name="priority",
            value=priority,
            weight=self.weights["priority"],
            weighted_value=priority * self.weights["priority"]
        ))
        
        # Performance (historical)
        performance = historical_performance.get(candidate.promotion.id, 0.5)
        scores.append(Score(
            name="performance",
            value=performance,
            weight=self.weights["performance"],
            weighted_value=performance * self.weights["performance"]
        ))
        
        # Pacing
        pacing_state = pacing_states.get(candidate.campaign_id)
        pacing = pacing_state.adjustment_factor if pacing_state else 1.0
        pacing = min(max(pacing, 0.0), 1.0)  # Normalize to [0, 1]
        scores.append(Score(
            name="pacing",
            value=pacing,
            weight=self.weights["pacing"],
            weighted_value=pacing * self.weights["pacing"]
        ))
        
        # Diversity (simplified)
        diversity = 0.5  # Default, should be calculated based on recent selections
        scores.append(Score(
            name="diversity",
            value=diversity,
            weight=self.weights["diversity"],
            weighted_value=diversity * self.weights["diversity"]
        ))
        
        return scores


# ============================================================================
# FREQUENCY CONTROLLER
# ============================================================================

class FrequencyController:
    """Controls frequency caps for promotions."""
    
    def __init__(self):
        """Initialize frequency controller."""
        self.counts: Dict[str, Dict[str, int]] = {}  # scope_key -> {promotion_id: count}
    
    def check_frequency(
        self,
        promotion_id: str,
        scope_key: str,
        frequency_cap: FrequencyCap
    ) -> bool:
        """
        Check if frequency cap is exceeded.
        
        Args:
            promotion_id: Promotion ID
            scope_key: Scope key (user_id, session_id, etc.)
            frequency_cap: Frequency cap configuration
        
        Returns:
            True if under cap, False if exceeded
        """
        current_count = self.counts.get(scope_key, {}).get(promotion_id, 0)
        return current_count < frequency_cap.max_impressions
    
    def record_impression(
        self,
        promotion_id: str,
        scope_key: str
    ) -> None:
        """Record an impression for frequency tracking."""
        if scope_key not in self.counts:
            self.counts[scope_key] = {}
        
        current = self.counts[scope_key].get(promotion_id, 0)
        self.counts[scope_key][promotion_id] = current + 1
    
    def get_count(self, promotion_id: str, scope_key: str) -> int:
        """Get current frequency count."""
        return self.counts.get(scope_key, {}).get(promotion_id, 0)


# ============================================================================
# BUDGET ENGINE
# ============================================================================

class BudgetEngine:
    """Manages campaign budgets."""
    
    def __init__(self):
        """Initialize budget engine."""
        self.budgets: Dict[str, Budget] = {}
    
    def get_budget(self, campaign_id: str) -> Optional[Budget]:
        """Get budget for campaign."""
        return self.budgets.get(campaign_id)
    
    def set_budget(self, budget: Budget) -> None:
        """Set budget for campaign."""
        self.budgets[budget.campaign_id] = budget
    
    def reserve(self, campaign_id: str, amount: Decimal) -> bool:
        """
        Reserve budget amount.
        
        Args:
            campaign_id: Campaign ID
            amount: Amount to reserve
        
        Returns:
            True if reserved, False if insufficient budget
        """
        budget = self.budgets.get(campaign_id)
        if not budget or not budget.can_serve(amount):
            return False
        
        budget.reserved += amount
        budget.last_updated = datetime.utcnow()
        return True
    
    def commit(self, campaign_id: str, amount: Decimal) -> bool:
        """
        Commit reserved budget to spent.
        
        Args:
            campaign_id: Campaign ID
            amount: Amount to commit
        
        Returns:
            True if committed, False if error
        """
        budget = self.budgets.get(campaign_id)
        if not budget:
            return False
        
        budget.reserved -= amount
        budget.spent += amount
        budget.last_updated = datetime.utcnow()
        return True
    
    def rollback(self, campaign_id: str, amount: Decimal) -> None:
        """Rollback reserved budget."""
        budget = self.budgets.get(campaign_id)
        if budget:
            budget.reserved -= amount
            budget.last_updated = datetime.utcnow()


# ============================================================================
# PACING ENGINE
# ============================================================================

class PacingEngine:
    """Controls budget pacing for campaigns."""
    
    def __init__(self):
        """Initialize pacing engine."""
        self.states: Dict[str, PacingState] = {}
    
    def get_pacing_state(self, campaign_id: str) -> Optional[PacingState]:
        """Get pacing state for campaign."""
        return self.states.get(campaign_id)
    
    def update_pacing(
        self,
        campaign_id: str,
        target_spend_rate: Decimal,
        current_spend_rate: Decimal
    ) -> PacingState:
        """
        Update pacing state.
        
        Args:
            campaign_id: Campaign ID
            target_spend_rate: Target spend rate per hour
            current_spend_rate: Current spend rate per hour
        
        Returns:
            Updated PacingState
        """
        # Calculate adjustment factor
        if current_spend_rate == Decimal("0"):
            adjustment_factor = 1.0
        else:
            ratio = current_spend_rate / target_spend_rate
            if ratio > 1.2:
                adjustment_factor = 0.8  # Slow down
            elif ratio < 0.8:
                adjustment_factor = 1.2  # Speed up
            else:
                adjustment_factor = 1.0  # On track
        
        state = PacingState(
            campaign_id=campaign_id,
            target_spend_rate=target_spend_rate,
            current_spend_rate=current_spend_rate,
            adjustment_factor=adjustment_factor
        )
        
        self.states[campaign_id] = state
        return state


# ============================================================================
# ATTRIBUTION ENGINE
# ============================================================================

class AttributionEngine:
    """Attributes conversions to interactions."""
    
    def attribute(
        self,
        conversion: Conversion,
        interactions: List[Interaction],
        model: str = "last_interaction"
    ) -> Optional[Attribution]:
        """
        Attribute conversion to interaction.
        
        Args:
            conversion: Conversion to attribute
            interactions: List of interactions
            model: Attribution model ("last_interaction", "first_interaction")
        
        Returns:
            Attribution record or None
        """
        if not interactions:
            return None
        
        # Sort by timestamp
        sorted_interactions = sorted(interactions, key=lambda x: x.timestamp)
        
        if model == "last_interaction":
            selected_interaction = sorted_interactions[-1]
        elif model == "first_interaction":
            selected_interaction = sorted_interactions[0]
        else:
            # Default to last
            selected_interaction = sorted_interactions[-1]
        
        attribution = Attribution(
            id=f"attr_{conversion.id}",
            conversion_id=conversion.id,
            campaign_id=conversion.campaign_id,
            promotion_id=conversion.promotion_id,
            interaction_id=selected_interaction.id,
            attribution_model=model,
            attributed_value=conversion.value
        )
        
        return attribution


# ============================================================================
# PROMOTION SERVICE (ORCHESTRATOR)
# ============================================================================

class PromotionService:
    """Main orchestration service for promotion decisions."""
    
    def __init__(self):
        """Initialize promotion service."""
        self.eligibility_engine = EligibilityEngine()
        self.candidate_generator = CandidateGenerator()
        self.context_engine = ContextEngine()
        self.ranking_engine = RankingEngine()
        self.frequency_controller = FrequencyController()
        self.budget_engine = BudgetEngine()
        self.pacing_engine = PacingEngine()
        self.attribution_engine = AttributionEngine()
        
        # Storage (in production, use repositories)
        self.campaigns: Dict[str, Campaign] = {}
        self.promotions: Dict[str, Promotion] = {}
        self.impressions: List[Impression] = []
        self.interactions: List[Interaction] = []
        self.conversions: List[Conversion] = []
        self.historical_performance: Dict[str, float] = {}
    
    def make_decision(
        self,
        placement: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **context_kwargs
    ) -> PromotionDecision:
        """
        Make a promotion decision.
        
        Args:
            placement: Placement ID
            user_id: Optional user ID
            session_id: Optional session ID
            **context_kwargs: Additional context
        
        Returns:
            PromotionDecision with selected promotion and explainability
        """
        # Build context
        context = self.context_engine.build_context(
            placement=placement,
            user_id=user_id,
            session_id=session_id,
            **context_kwargs
        )
        
        # Generate candidates
        all_candidates = self.candidate_generator.generate_candidates(
            list(self.promotions.values()),
            self.campaigns,
            context
        )
        
        # Check eligibility
        eligible_candidates = []
        filtered_out = []
        
        for candidate in all_candidates:
            scope_key = user_id or session_id or "anonymous"
            frequency_counts = {candidate.promotion.id: self.frequency_controller.get_count(candidate.promotion.id, scope_key)}
            budget = self.budget_engine.get_budget(candidate.campaign_id)
            
            if not budget:
                filtered_out.append({
                    "promotion_id": candidate.promotion.id,
                    "reason": "NO_BUDGET"
                })
                continue
            
            eligibility = self.eligibility_engine.check_eligibility(
                candidate.promotion,
                candidate.campaign,
                context,
                budget,
                frequency_counts
            )
            
            candidate.eligibility = eligibility
            
            if eligibility.eligible:
                eligible_candidates.append(candidate)
            else:
                filtered_out.append({
                    "promotion_id": candidate.promotion.id,
                    "reason_codes": eligibility.reason_codes
                })
        
        # Rank candidates
        pacing_states = {
            cid: self.pacing_engine.get_pacing_state(cid)
            for cid in self.campaigns.keys()
        }
        pacing_states = {k: v for k, v in pacing_states.items() if v is not None}
        
        ranking_results = self.ranking_engine.rank(
            eligible_candidates,
            self.historical_performance,
            pacing_states
        )
        
        # Select winner
        selected_promotion = None
        if ranking_results:
            selected_promotion = ranking_results[0].candidate.promotion
        
        # Create decision
        decision = PromotionDecision(
            id=f"dec_{datetime.utcnow().timestamp()}",
            decision_type=DecisionType.SPONSORED_PROMOTION if selected_promotion else DecisionType.ORGANIC_RECOMMENDATION,
            selected_promotion=selected_promotion,
            all_candidates=all_candidates,
            ranking_results=ranking_results,
            filtered_out=filtered_out,
            context=context
        )
        
        return decision
    
    def record_impression(
        self,
        decision: PromotionDecision,
        session_reference: str
    ) -> Optional[Impression]:
        """Record an impression."""
        if not decision.selected_promotion:
            return None
        
        impression = Impression(
            id=f"imp_{datetime.utcnow().timestamp()}",
            promotion_id=decision.selected_promotion.id,
            campaign_id=decision.selected_promotion.campaign_id,
            placement=decision.context.get("placement", ""),
            timestamp=datetime.utcnow(),
            session_reference=session_reference,
            context_reference=decision.id,
            decision_id=decision.id
        )
        
        self.impressions.append(impression)
        
        # Update frequency
        scope_key = decision.context.get("user_id") or decision.context.get("session_id") or "anonymous"
        self.frequency_controller.record_impression(decision.selected_promotion.id, scope_key)
        
        return impression
    
    def record_interaction(
        self,
        impression_id: str,
        interaction_type: InteractionType,
        session_reference: str
    ) -> Optional[Interaction]:
        """Record an interaction."""
        impression = next((imp for imp in self.impressions if imp.id == impression_id), None)
        if not impression:
            return None
        
        interaction = Interaction(
            id=f"int_{datetime.utcnow().timestamp()}",
            impression_id=impression_id,
            promotion_id=impression.promotion_id,
            campaign_id=impression.campaign_id,
            interaction_type=interaction_type,
            timestamp=datetime.utcnow(),
            session_reference=session_reference
        )
        
        self.interactions.append(interaction)
        return interaction
    
    def record_conversion(
        self,
        campaign_id: str,
        promotion_id: str,
        event_type: str,
        value: Decimal,
        currency: str,
        reference: str
    ) -> Conversion:
        """Record a conversion."""
        conversion = Conversion(
            id=f"conv_{datetime.utcnow().timestamp()}",
            campaign_id=campaign_id,
            promotion_id=promotion_id,
            event_type=event_type,
            value=value,
            currency=currency,
            timestamp=datetime.utcnow(),
            reference=reference,
            status=ConversionStatus.CONFIRMED
        )
        
        self.conversions.append(conversion)
        return conversion
