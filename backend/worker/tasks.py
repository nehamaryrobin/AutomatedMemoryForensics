import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from worker.celery_app import celery_app
from app.models.case import Case, AnalysisJob
import uuid
import datetime

# Since the worker is a separate process and might not run in an async loop naturally without async setup,
# we use synchronous SQLAlchemy engine for the background worker to safely write to the DB.
SYNC_DATABASE_URI = "postgresql://sih_user:sih_password@localhost:5432/forensics_db"
engine = create_engine(SYNC_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@celery_app.task(bind=True)
def analyze_memory_dump(self, case_id: str, storage_path: str):
    """
    Simulates memory analysis for Phase 2.
    In Phase 3, this will execute Volatility 3 plugins.
    """
    db = SessionLocal()
    try:
        # Create an AnalysisJob record
        job_id = str(uuid.uuid4())
        job = AnalysisJob(
            id=job_id,
            case_id=case_id,
            status="RUNNING",
            started_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.add(job)
        
        # Update case status
        case = db.query(Case).filter(Case.id == case_id).first()
        if case:
            case.status = "RUNNING"
            
        db.commit()

        # Simulate time-consuming forensic analysis
        time.sleep(5)
        
        # Mark as completed
        job.status = "COMPLETED"
        job.completed_at = datetime.datetime.now(datetime.timezone.utc)
        
        if case:
            case.status = "COMPLETED"
            case.risk_score = 45.5 # Simulated risk score
            
        db.commit()
        return {"status": "success", "job_id": job_id, "case_id": case_id}
        
    except Exception as e:
        db.rollback()
        # Mark as failed
        case = db.query(Case).filter(Case.id == case_id).first()
        if case:
            case.status = "FAILED"
            db.commit()
        raise e
    finally:
        db.close()
