from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.storage import LocalObjectStore
from app.services.analysis import run_memory_analysis
from app.models.case import Case
from app.schemas.case import UploadResponse
import uuid

router = APIRouter()
storage_service = LocalObjectStore()

@router.post("/upload", response_model=UploadResponse)
async def upload_memory_dump(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    case_id = str(uuid.uuid4())
    
    # Save file to storage
    file_metadata = await storage_service.save_upload_file(file, case_id)
    
    # Create Case record
    new_case = Case(
        id=case_id,
        filename=file_metadata["filename"],
        file_size=file_metadata["file_size"],
        sha256=file_metadata["sha256"],
        storage_path=file_metadata["storage_path"],
        status="QUEUED",
        risk_score=0.0
    )
    
    db.add(new_case)
    await db.commit()
    
    # Trigger Background Task for automated Volatility analysis
    background_tasks.add_task(run_memory_analysis, case_id, file_metadata["storage_path"])
    
    return UploadResponse(
        case_id=case_id,
        message="Upload successful, analysis queued."
    )
