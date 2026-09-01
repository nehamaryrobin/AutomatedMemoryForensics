import json

def detect_hidden_processes(pslist_data: list, psscan_data: list, psxview_data: list) -> list:
    """
    Cross-references process enumeration plugins to find hidden processes.
    A process is considered 'hidden' if it is found by pool tag scanning (psscan) 
    or cross-view analysis (psxview) but is missing from the active process list (pslist).
    """
    findings = []
    
    # 1. Extract PIDs known to the OS (pslist)
    # Volatility JSON outputs are lists of dictionaries
    pslist_pids = set()
    for proc in pslist_data:
        # Depending on the vol3 output, the key is usually 'PID'
        pid = proc.get("PID")
        if pid is not None:
            pslist_pids.add(pid)
            
    hidden_pids = set()

    # 2. Check psscan for missing PIDs
    for proc in psscan_data:
        pid = proc.get("PID")
        if pid is not None and pid > 4 and pid not in pslist_pids: # Ignore PID 0, 4 (System)
            hidden_pids.add(pid)
            name = proc.get("ImageFileName", "Unknown")
            findings.append({
                "finding_type": "HIDDEN_PROCESS",
                "severity": "HIGH",
                "description": f"Potential hidden process: {name} (PID {pid}). Process found by memory scanning (psscan) but absent from standard process list (pslist). Indicates Direct Kernel Object Manipulation (DKOM).",
                "confidence": 0.9,
                "evidence_data": json.dumps({"source": "psscan", "process_info": proc})
            })
            
    # 3. Check psxview for missing PIDs
    for proc in psxview_data:
        pid = proc.get("PID")
        if pid is not None and pid > 4 and pid not in pslist_pids and pid not in hidden_pids:
            name = proc.get("ImageFileName", "Unknown")
            findings.append({
                "finding_type": "HIDDEN_PROCESS",
                "severity": "HIGH",
                "description": f"Potential hidden process: {name} (PID {pid}). Process flagged by psxview but absent from standard process list. Indicates rootkit activity.",
                "confidence": 0.85,
                "evidence_data": json.dumps({"source": "psxview", "process_info": proc})
            })

    return findings

def detect_injected_code(malfind_data: list) -> list:
    """
    Analyzes the output of windows.malfind.Malfind to identify injected VAD segments.
    """
    findings = []
    
    for proc in malfind_data:
        pid = proc.get("PID")
        name = proc.get("Process", "Unknown")
        protection = proc.get("Protection", "")
        
        # Malfind explicitly looks for PAGE_EXECUTE_READWRITE and similar suspicious protections
        if pid is not None:
            findings.append({
                "finding_type": "INJECTED_CODE",
                "severity": "HIGH",
                "description": f"Injected code detected in {name} (PID {pid}). Memory segment has suspicious protections: {protection}.",
                "confidence": 0.85,
                "evidence_data": json.dumps({"source": "malfind", "process_info": proc})
            })
            
    return findings

def detect_unlinked_dlls(ldrmodules_data: list) -> list:
    """
    Analyzes windows.ldrmodules.LdrModules output to identify DLLs that are present in memory 
    but unlinked from standard PEB lists (InLoad, InInit, InMem), indicating DLL injection.
    """
    findings = []
    
    for mod in ldrmodules_data:
        pid = mod.get("PID")
        process_name = mod.get("Process", "Unknown")
        mapped_path = mod.get("MappedPath", "")
        
        in_load = mod.get("InLoad")
        in_init = mod.get("InInit")
        in_mem = mod.get("InMem")
        
        # Ignore empty or strictly system mapped paths that are naturally not in lists (like free memory)
        if pid and mapped_path and mapped_path.lower() != "wow64":
            # If a module is False in any of the PEB lists but has a mapped path
            if in_load is False or in_init is False or in_mem is False:
                findings.append({
                    "finding_type": "UNLINKED_DLL",
                    "severity": "MEDIUM",
                    "description": f"Unlinked DLL detected in {process_name} (PID {pid}). Module '{mapped_path}' is mapped in memory but missing from PEB lists (InLoad: {in_load}, InInit: {in_init}, InMem: {in_mem}).",
                    "confidence": 0.75,
                    "evidence_data": json.dumps({"source": "ldrmodules", "module_info": mod})
                })
                
    return findings

def detect_suspicious_network(netscan_data: list, suspicious_pids: set) -> list:
    """
    Correlates active network connections (netscan) with processes already flagged as suspicious 
    (hidden, injected, etc). If a malicious process has a network connection, it is a high-confidence C2 indicator.
    """
    findings = []
    
    for net in netscan_data:
        pid = net.get("PID")
        
        # If this PID was flagged by a previous memory forensic check
        if pid in suspicious_pids:
            local_addr = net.get("LocalAddr", "")
            local_port = net.get("LocalPort", "")
            remote_addr = net.get("ForeignAddr", "")
            remote_port = net.get("ForeignPort", "")
            state = net.get("State", "")
            
            # We care about active connections or listening ports
            if remote_addr and remote_addr != "0.0.0.0" and remote_addr != "::" and remote_addr != "*":
                description = f"CRITICAL: Suspicious process (PID {pid}) is communicating with remote address {remote_addr}:{remote_port} (State: {state}). High probability of Command and Control (C2) activity."
            else:
                description = f"CRITICAL: Suspicious process (PID {pid}) is listening on local port {local_port}. Potential backdoor/bind shell."
                
            findings.append({
                "finding_type": "SUSPICIOUS_NETWORK",
                "severity": "CRITICAL",
                "description": description,
                "confidence": 0.95,
                "evidence_data": json.dumps({"source": "netscan", "network_info": net})
            })
            
    return findings
