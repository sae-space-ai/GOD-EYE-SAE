"""
SAE Promotion Engine - API Endpoints.

This module implements HTTP API endpoints for the Promotion Engine.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from ..persistence import get_session
from ..security.authentication import get_current_user
from ..persistence.models import User as UserModel
from .models import (
    Campaign, Promotion, CampaignStatus, PromotionStatus,
)
from .engine import PromotionService

router = APIRouter(prefix="/api/v1/promotions", tags=["promotions"])

# In-memory service (in production, use dependency injection)
promotion_service = PromotionService()


# ============================================================================
# CAMPAIGNS
# ============================================================================

@router.get("/campaigns")
async def list_campaigns(
    status_filter: Optional[CampaignStatus] = None,
    current_user: UserModel = Depends(get_current_user)
):
    """List all campaigns."""
    campaigns = list(promotion_service.campaigns.values())
    
    if status_filter:
        campaigns = [c for c in campaigns if c.status == status_filter]
    
    return {
        "campaigns": [
            {
                "id": c.id,
                "name": c.name,
                "status": c.status.value,
                "advertiser_or_owner": c.advertiser_or_owner,
                "objective": c.objective,
                "start_at": c.start_at.isoformat(),
                "end_at": c.end_at.isoformat(),
                "budget": str(c.budget),
                "priority": c.priority,
                "created_at": c.created_at.isoformat(),
            }
            for c in campaigns
        ],
        "total": len(campaigns)
    }


@router.post("/campaigns")
async def create_campaign(
    name: str,
    advertiser_or_owner: str,
    objective: str,
    start_at: datetime,
    end_at: datetime,
    budget: Decimal,
    priority: int = 5,
    current_user: UserModel = Depends(get_current_user)
):
    """Create a new campaign."""
    from ..common.enums import generate_id
    
    campaign = Campaign(
        id=generate_id(),
        name=name,
        status=CampaignStatus.DRAFT,
        advertiser_or_owner=advertiser_or_owner,
        objective=objective,
        start_at=start_at,
        end_at=end_at,
        budget=budget,
        priority=priority
    )
    
    promotion_service.campaigns[campaign.id] = campaign
    
    return {
        "id": campaign.id,
        "status": "created",
        "campaign": {
            "id": campaign.id,
            "name": campaign.name,
            "status": campaign.status.value,
        }
    }


@router.post("/campaigns/{campaign_id}/activate")
async def activate_campaign(
    campaign_id: str,
    current_user: UserModel = Depends(get_current_user)
):
    """Activate a campaign."""
    campaign = promotion_service.campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    if campaign.status != CampaignStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign must be in DRAFT status to activate"
        )
    
    campaign.status = CampaignStatus.ACTIVE
    campaign.updated_at = datetime.utcnow()
    
    return {
        "id": campaign.id,
        "status": "activated"
    }


# ============================================================================
# PROMOTIONS
# ============================================================================

@router.get("/")
async def list_promotions(
    campaign_id: Optional[str] = None,
    current_user: UserModel = Depends(get_current_user)
):
    """List all promotions."""
    promotions = list(promotion_service.promotions.values())
    
    if campaign_id:
        promotions = [p for p in promotions if p.campaign_id == campaign_id]
    
    return {
        "promotions": [
            {
                "id": p.id,
                "campaign_id": p.campaign_id,
                "title": p.title,
                "status": p.status.value,
                "placement": p.placement,
                "priority": p.priority,
                "created_at": p.created_at.isoformat(),
            }
            for p in promotions
        ],
        "total": len(promotions)
    }


@router.post("/")
async def create_promotion(
    campaign_id: str,
    title: str,
    description: str,
    creative_reference: str,
    destination: str,
    placement: str,
    priority: int = 5,
    current_user: UserModel = Depends(get_current_user)
):
    """Create a new promotion."""
    from ..common.enums import generate_id
    
    campaign = promotion_service.campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    promotion = Promotion(
        id=generate_id(),
        campaign_id=campaign_id,
        title=title,
        description=description,
        creative_reference=creative_reference,
        destination=destination,
        placement=placement,
        status=PromotionStatus.ACTIVE,
        priority=priority
    )
    
    promotion_service.promotions[promotion.id] = promotion
    
    return {
        "id": promotion.id,
        "status": "created",
        "promotion": {
            "id": promotion.id,
            "title": promotion.title,
            "status": promotion.status.value,
        }
    }


# ============================================================================
# PROMOTION DECISIONS
# ============================================================================

@router.post("/decisions")
async def make_promotion_decision(
    placement: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    current_user: UserModel = Depends(get_current_user)
):
    """Make a promotion decision."""
    decision = promotion_service.make_decision(
        placement=placement,
        user_id=user_id,
        session_id=session_id
    )
    
    return {
        "decision_id": decision.id,
        "decision_type": decision.decision_type.value,
        "selected_promotion": {
            "id": decision.selected_promotion.id,
            "title": decision.selected_promotion.title,
            "campaign_id": decision.selected_promotion.campaign_id,
        } if decision.selected_promotion else None,
        "total_candidates": len(decision.all_candidates),
        "eligible_candidates": len(decision.ranking_results),
        "filtered_out": len(decision.filtered_out),
        "timestamp": decision.timestamp.isoformat(),
        "algorithm_version": decision.algorithm_version,
    }


# ============================================================================
# IMPRESSIONS
# ============================================================================

@router.post("/impressions")
async def record_impression(
    decision_id: str,
    session_reference: str,
    current_user: UserModel = Depends(get_current_user)
):
    """Record an impression."""
    # Find decision (in production, use repository)
    # For now, create a mock decision
    from .models import PromotionDecision, DecisionType
    
    decision = PromotionDecision(
        id=decision_id,
        decision_type=DecisionType.SPONSORED_PROMOTION,
        selected_promotion=list(promotion_service.promotions.values())[0] if promotion_service.promotions else None,
        context={"placement": "test"}
    )
    
    impression = promotion_service.record_impression(decision, session_reference)
    
    if not impression:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No promotion selected for impression"
        )
    
    return {
        "impression_id": impression.id,
        "promotion_id": impression.promotion_id,
        "timestamp": impression.timestamp.isoformat()
    }


# ============================================================================
# INTERACTIONS
# ============================================================================

@router.post("/interactions")
async def record_interaction(
    impression_id: str,
    interaction_type: str,
    session_reference: str,
    current_user: UserModel = Depends(get_current_user)
):
    """Record an interaction."""
    from .models import InteractionType
    
    try:
        int_type = InteractionType(interaction_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid interaction type: {interaction_type}"
        )
    
    interaction = promotion_service.record_interaction(
        impression_id, int_type, session_reference
    )
    
    if not interaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Impression not found"
        )
    
    return {
        "interaction_id": interaction.id,
        "interaction_type": interaction.interaction_type.value,
        "timestamp": interaction.timestamp.isoformat()
    }


# ============================================================================
# CONVERSIONS
# ============================================================================

@router.post("/conversions")
async def record_conversion(
    campaign_id: str,
    promotion_id: str,
    event_type: str,
    value: Decimal,
    currency: str,
    reference: str,
    current_user: UserModel = Depends(get_current_user)
):
    """Record a conversion."""
    conversion = promotion_service.record_conversion(
        campaign_id=campaign_id,
        promotion_id=promotion_id,
        event_type=event_type,
        value=value,
        currency=currency,
        reference=reference
    )
    
    return {
        "conversion_id": conversion.id,
        "status": conversion.status.value,
        "timestamp": conversion.timestamp.isoformat()
    }


# ============================================================================
# ANALYTICS
# ============================================================================

@router.get("/analytics")
async def get_analytics(
    campaign_id: Optional[str] = None,
    current_user: UserModel = Depends(get_current_user)
):
    """Get promotion analytics."""
    impressions = promotion_service.impressions
    interactions = promotion_service.interactions
    conversions = promotion_service.conversions
    
    if campaign_id:
        impressions = [i for i in impressions if i.campaign_id == campaign_id]
        interactions = [i for i in interactions if i.campaign_id == campaign_id]
        conversions = [c for c in conversions if c.campaign_id == campaign_id]
    
    # Calculate metrics
    total_impressions = len(impressions)
    total_interactions = len(interactions)
    total_conversions = len(conversions)
    
    ctr = (total_interactions / total_impressions * 100) if total_impressions > 0 else 0
    conversion_rate = (total_conversions / total_impressions * 100) if total_impressions > 0 else 0
    
    return {
        "impressions": total_impressions,
        "interactions": total_interactions,
        "conversions": total_conversions,
        "ctr": round(ctr, 2),
        "conversion_rate": round(conversion_rate, 2),
        "timestamp": datetime.utcnow().isoformat()
    }
