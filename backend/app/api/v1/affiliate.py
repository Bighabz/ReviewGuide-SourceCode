"""
Affiliate Click Tracking API

Provides endpoint to track affiliate link clicks for analytics.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logger import get_logger
from app.core.database import get_db
from app.core.dependencies import check_rate_limit
from app.models.affiliate_click import AffiliateClick

logger = get_logger(__name__)
router = APIRouter()


class ClickRequest(BaseModel):
    """Affiliate click tracking request"""
    provider: str = Field(..., max_length=100, description="Affiliate provider name")
    product_name: Optional[str] = Field(None, max_length=500, description="Product name")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    url: str = Field(..., max_length=2048, description="Affiliate URL clicked")
    session_id: Optional[str] = Field(None, max_length=255, description="User session ID")


class ClickResponse(BaseModel):
    """Affiliate click tracking response"""
    tracked: bool


@router.post("/click", response_model=ClickResponse, dependencies=[Depends(check_rate_limit)])
async def track_click(request: ClickRequest, db: AsyncSession = Depends(get_db)):
    """Track an affiliate link click"""
    try:
        click = AffiliateClick(
            session_id=request.session_id,
            provider=request.provider,
            product_name=request.product_name,
            category=request.category,
            url=request.url,
        )
        db.add(click)
        await db.commit()
        logger.info(f"Tracked affiliate click: {request.provider} - {request.product_name}")
        return ClickResponse(tracked=True)
    except Exception as e:
        logger.error(f"Failed to track affiliate click: {e}")
        await db.rollback()
        return ClickResponse(tracked=False)
