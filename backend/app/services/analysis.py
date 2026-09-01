import os
import datetime
import uuid
import json
import logging
from app.core.database import SyncSessionLocal
from app.models.case import Case, AnalysisJob, PluginResult, EvidenceMetadata
from app.services.forensics.vol_wrapper import VolatilityWrapper
from app.services.forensics.detection import (
    detect_hidden_processes,
    detect_injected_code,
    detect_unlinked_dlls,
    detect_suspicious_network,
)

logger = logging.getLogger(__name__)

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

def run_memory_analysis(case_id: str, storage_path: str):
    """
    Background task that executes Volatility 3 plugins and anomaly detection.
    Runs synchronously in a background thread spawned by FastAPI BackgroundTasks.
    """
    logger.info(f"Starting background memory analysis for case: {case_id}")
    db = SyncSessionLocal()
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
        case_dir = os.path.dirname(storage_path)
        results_dir = os.path.join(case_dir, "results")

        plugin_outputs = {}
        successful_plugins = 0

        # 3. Execute Plugins
        for plugin in WINDOWS_PLUGINS:
            logger.info(f"Running plugin {plugin} for case {case_id}...")
            result_data = vol.run_plugin(storage_path, plugin, results_dir)
            
            if result_data["status"] == "SUCCESS" and result_data["parsed_output"]:
                try:
                    plugin_outputs[plugin] = json.loads(result_data["parsed_output"])
                except Exception:
                    plugin_outputs[plugin] = []
            else:
                plugin_outputs[plugin] = []
            
            # Save plugin result in DB
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
                
        db.commit()

        # 4. Run Heuristic Detection Engine
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
        
        # 5. Network Correlation
        suspicious_pids = set()
        for finding in findings:
            try:
                data = json.loads(finding["evidence_data"])
                pid = None
                if "process_info" in data:
                    pid = data["process_info"].get("PID")
                elif "module_info" in data:
                    pid = data["module_info"].get("PID")
                
                if pid is not None:
                    suspicious_pids.add(pid)
            except Exception:
                pass
                
        findings.extend(detect_suspicious_network(
            netscan_data=plugin_outputs.get("windows.netscan.NetScan", []),
            suspicious_pids=suspicious_pids
        ))
        
        # 6. Save Evidence Metadata & Compute Risk Score
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
            
            if finding["finding_type"] == "HIDDEN_PROCESS":
                risk_score += 30.0
            elif finding["finding_type"] == "INJECTED_CODE":
                risk_score += 25.0
            elif finding["finding_type"] == "UNLINKED_DLL":
                risk_score += 20.0
            elif finding["finding_type"] == "SUSPICIOUS_NETWORK":
                risk_score += 40.0

        db.commit()

        # 7. Finalize Job Status
        job.status = "COMPLETED"
        job.completed_at = datetime.datetime.now(datetime.timezone.utc)
        
        if case:
            if successful_plugins > 0:
                case.status = "COMPLETED"
                case.risk_score = min(100.0, risk_score)
            else:
                case.status = "FAILED"
                
        db.commit()
        logger.info(f"Analysis completed for case {case_id}. Risk score: {case.risk_score if case else 'N/A'}")
        
    except Exception as e:
        logger.error(f"Error analyzing case {case_id}: {e}", exc_info=True)
        db.rollback()
        case = db.query(Case).filter(Case.id == case_id).first()
        if case:
            case.status = "FAILED"
            db.commit()
    finally:
        db.close()
