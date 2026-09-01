from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.case import Case
from app.schemas.case import CaseResponse

router = APIRouter()

@router.get("/{case_id}", response_model=CaseResponse)
async def get_case_status(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Case).filter(Case.id == case_id))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    return case
