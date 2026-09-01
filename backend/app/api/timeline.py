from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.case import TimelineEvent
from typing import List, Dict, Any

router = APIRouter()

@router.get("/{case_id}/timeline", response_model=List[Dict[str, Any]])
async def get_case_timeline(case_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns all TimelineEvents associated with a given case, sorted chronologically.
    """
    result = await db.execute(
        select(TimelineEvent)
        .filter(TimelineEvent.case_id == case_id)
        .order_by(TimelineEvent.timestamp.asc())
    )
    events = result.scalars().all()
    
    formatted_events = []
    for e in events:
        formatted_events.append({
            "id": e.id,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "event_type": e.event_type,
            "details": e.details
        })
        
    return formatted_events
