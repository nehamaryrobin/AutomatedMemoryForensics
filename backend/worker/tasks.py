import os
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from worker.celery_app import celery_app
from app.models.case import Case, AnalysisJob, PluginResult
from worker.forensics.vol_wrapper import VolatilityWrapper
import uuid

# Synchronous DB setup for the worker
SYNC_DATABASE_URI = "postgresql://sih_user:sih_password@localhost:5432/forensics_db"
engine = create_engine(SYNC_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# The selected plugins for the MVP Phase 3
WINDOWS_PLUGINS = [
    "windows.pslist.PsList",
    "windows.psscan.PsScan",
    "windows.pstree.PsTree",
    "windows.psxview.PsXView",
    "windows.dlllist.DllList",
    "windows.ldrmodules.LdrModules",
    "windows.malfind.Malfind",
    "windows.netscan.NetScan",
    "windows.cmdline.CmdLine",
    "windows.handles.Handles",
    "windows.vadinfo.VadInfo",
    "windows.modules.Modules"
]

@celery_app.task(bind=True)
def analyze_memory_dump(self, case_id: str, storage_path: str):
    """
    Executes Volatility 3 plugins on the uploaded memory dump.
    """
    db = SessionLocal()
    try:
        # 1. Update Job Status to RUNNING
        job_id = str(uuid.uuid4())
        job = AnalysisJob(
            id=job_id,
            case_id=case_id,
            status="RUNNING",
            started_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.add(job)
        
        case = db.query(Case).filter(Case.id == case_id).first()
        if case:
            case.status = "RUNNING"
            
        db.commit()

        # 2. Initialize Volatility Wrapper
        vol = VolatilityWrapper()
        
        # We will store the output JSONs in a 'results' folder inside the case storage dir
        case_dir = os.path.dirname(storage_path)
        results_dir = os.path.join(case_dir, "results")

        # 3. Iterate and execute plugins
        successful_plugins = 0
        for plugin in WINDOWS_PLUGINS:
            # Run the plugin
            result_data = vol.run_plugin(storage_path, plugin, results_dir)
            
            # Save the result metadata to the DB
            db_result = PluginResult(
                id=str(uuid.uuid4()),
                case_id=case_id,
                plugin_name=result_data["plugin_name"],
                status=result_data["status"],
                execution_time=result_data["execution_time"],
                raw_output_path=result_data["raw_output_path"],
                # We truncate parsed_output to prevent DB overflow if it's too large, 
                # but it's safe on disk either way.
                parsed_output=result_data["parsed_output"] if result_data["parsed_output"] else result_data.get("error", "")
            )
            db.add(db_result)
            
            if result_data["status"] == "SUCCESS":
                successful_plugins += 1
                
        # Commit all plugin results
        db.commit()

        # 4. Finalize Job Status
        job.status = "COMPLETED"
        job.completed_at = datetime.datetime.now(datetime.timezone.utc)
        
        if case:
            # If at least one plugin succeeded, consider the extraction completed.
            if successful_plugins > 0:
                case.status = "COMPLETED"
                # Keep risk score 0 for now until Phase 4 (Detection/Correlation)
                case.risk_score = 0.0 
            else:
                case.status = "FAILED"
                
        db.commit()
        return {"status": "success", "job_id": job_id, "case_id": case_id, "successful_plugins": successful_plugins}
        
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
