from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.case import EvidenceMetadata
from typing import List, Dict, Any

router = APIRouter()

@router.get("/{case_id}/findings", response_model=List[Dict[str, Any]])
async def get_case_findings(case_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns all EvidenceMetadata findings associated with a given case.
    """
    result = await db.execute(select(EvidenceMetadata).filter(EvidenceMetadata.case_id == case_id))
    findings = result.scalars().all()
    
    # We return dictionaries to easily handle the json strings
    formatted_findings = []
    for f in findings:
        formatted_findings.append({
            "id": f.id,
            "finding_type": f.finding_type,
            "severity": f.severity,
            "description": f.description,
            "confidence": f.confidence,
            "evidence_data": f.evidence_data
        })
        
    return formatted_findings
