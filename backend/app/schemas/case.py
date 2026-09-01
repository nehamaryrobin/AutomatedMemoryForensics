from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class CaseBase(BaseModel):
    filename: str
    file_size: int
    sha256: str
    status: str
    risk_score: float

class CaseCreate(CaseBase):
    storage_path: str

class CaseResponse(CaseBase):
    id: str
    created_at: datetime
    
    class Config:
        orm_mode = True
        from_attributes = True

class UploadResponse(BaseModel):
    case_id: str
    message: str
