import os
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from worker.celery_app import celery_app
from app.models.case import Case, AnalysisJob, PluginResult, EvidenceMetadata, TimelineEvent
from worker.forensics.vol_wrapper import VolatilityWrapper
from worker.forensics.detection import detect_hidden_processes, detect_injected_code, detect_unlinked_dlls, detect_suspicious_network
from worker.forensics.timeline import generate_timeline
import uuid
import json

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

        # Dictionary to hold parsed JSONs for the detection engine
        plugin_outputs = {}

        # 3. Iterate and execute plugins
        successful_plugins = 0
        for plugin in WINDOWS_PLUGINS:
            # Run the plugin
            result_data = vol.run_plugin(storage_path, plugin, results_dir)
            
            # Store in dict for detection phase
            if result_data["status"] == "SUCCESS" and result_data["parsed_output"]:
                try:
                    plugin_outputs[plugin] = json.loads(result_data["parsed_output"])
                except:
                    plugin_outputs[plugin] = []
            else:
                plugin_outputs[plugin] = []
            
            # Save the result metadata to the DB
            db_result = PluginResult(
                id=str(uuid.uuid4()),
                case_id=case_id,
                plugin_name=result_data["plugin_name"],
                status=result_data["status"],
                execution_time=result_data["execution_time"],
                raw_output_path=result_data["raw_output_path"],
                parsed_output=result_data["parsed_output"] if result_data["parsed_output"] else result_data.get("error", "")
            )
            db.add(db_result)
            
            if result_data["status"] == "SUCCESS":
                successful_plugins += 1
                
        # Commit all plugin results
        db.commit()

        # 4. Phase 4, 5, 6: Run Detection Engine (Cross-View Analysis & Injection)
        findings = detect_hidden_processes(
            pslist_data=plugin_outputs.get("windows.pslist.PsList", []),
            psscan_data=plugin_outputs.get("windows.psscan.PsScan", []),
            psxview_data=plugin_outputs.get("windows.psxview.PsXView", [])
        )
        
        findings.extend(detect_injected_code(
            malfind_data=plugin_outputs.get("windows.malfind.Malfind", [])
        ))
        
        findings.extend(detect_unlinked_dlls(
            ldrmodules_data=plugin_outputs.get("windows.ldrmodules.LdrModules", [])
        ))
        
        # 5. Phase 7: Network Correlation
        suspicious_pids = set()
        for finding in findings:
            data = json.loads(finding["evidence_data"])
            pid = None
            if "process_info" in data:
                pid = data["process_info"].get("PID")
            elif "module_info" in data:
                pid = data["module_info"].get("PID")
            
            if pid is not None:
                suspicious_pids.add(pid)
                
        findings.extend(detect_suspicious_network(
            netscan_data=plugin_outputs.get("windows.netscan.NetScan", []),
            suspicious_pids=suspicious_pids
        ))
        
        risk_score = 0.0
        for finding in findings:
            evidence = EvidenceMetadata(
                id=str(uuid.uuid4()),
                case_id=case_id,
                finding_type=finding["finding_type"],
                severity=finding["severity"],
                description=finding["description"],
                confidence=finding["confidence"],
                evidence_data=finding["evidence_data"]
            )
            db.add(evidence)
            
            # Increment Risk Score based on finding type
            if finding["finding_type"] == "HIDDEN_PROCESS":
                risk_score += 30.0
            elif finding["finding_type"] == "INJECTED_CODE":
                risk_score += 25.0
            elif finding["finding_type"] == "UNLINKED_DLL":
                risk_score += 20.0
            elif finding["finding_type"] == "SUSPICIOUS_NETWORK":
                risk_score += 40.0

        # 6. Phase 8: Timeline Generation
        timeline_events = generate_timeline(plugin_outputs)
        for event in timeline_events:
            te = TimelineEvent(
                id=str(uuid.uuid4()),
                case_id=case_id,
                timestamp=event["timestamp"],
                event_type=event["event_type"],
                details=event["details"]
            )
            db.add(te)

        db.commit()

        # 7. Finalize Job Status
        job.status = "COMPLETED"
        job.completed_at = datetime.datetime.now(datetime.timezone.utc)
        
        if case:
            if successful_plugins > 0:
                case.status = "COMPLETED"
                # Cap risk score at 100
                case.risk_score = min(100.0, risk_score)
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
