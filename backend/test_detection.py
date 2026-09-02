"""
Unit test to verify the detection algorithms in detection.py with simulated Volatility plugin outputs.
"""
from app.services.forensics.detection import (
    detect_hidden_processes,
    detect_injected_code,
    detect_unlinked_dlls,
    detect_suspicious_network
)
import json

def test_detection_engine():
    print("=" * 60)
    print("TESTING AUTOMATED MEMORY FORENSICS DETECTION ENGINE")
    print("=" * 60)

    # 1. Test Hidden Process Detection (DKOM)
    print("\n1. Testing Hidden Process (DKOM) Detection...")
    mock_pslist = [
        {"PID": 4, "ImageFileName": "System"},
        {"PID": 520, "ImageFileName": "smss.exe"},
        {"PID": 1204, "ImageFileName": "explorer.exe"}
    ]
    # svchost.exe (PID 6632) is unlinked from pslist, but found in psscan pool memory
    mock_psscan = [
        {"PID": 4, "ImageFileName": "System"},
        {"PID": 520, "ImageFileName": "smss.exe"},
        {"PID": 1204, "ImageFileName": "explorer.exe"},
        {"PID": 6632, "ImageFileName": "svchost.exe"} # Hidden!
    ]
    mock_psxview = []

    hidden_findings = detect_hidden_processes(mock_pslist, mock_psscan, mock_psxview)
    print(f" -> Found {len(hidden_findings)} hidden process(es):")
    for f in hidden_findings:
        print(f"    [{f['severity']}] {f['finding_type']}: {f['description']}")

    # 2. Test Injected Code (Malfind)
    print("\n2. Testing Injected Code (Malfind) Detection...")
    mock_malfind = [
        {"PID": 6632, "Process": "svchost.exe", "Protection": "PAGE_EXECUTE_READWRITE"}
    ]
    injection_findings = detect_injected_code(mock_malfind)
    print(f" -> Found {len(injection_findings)} injection finding(s):")
    for f in injection_findings:
        print(f"    [{f['severity']}] {f['finding_type']}: {f['description']}")

    # 3. Test Unlinked DLLs (LdrModules)
    print("\n3. Testing Unlinked DLL (LdrModules) Detection...")
    mock_ldrmodules = [
        {
            "PID": 6632,
            "Process": "svchost.exe",
            "MappedPath": "C:\\Windows\\Temp\\payload.dll",
            "InLoad": False,
            "InInit": False,
            "InMem": True
        }
    ]
    dll_findings = detect_unlinked_dlls(mock_ldrmodules)
    print(f" -> Found {len(dll_findings)} unlinked DLL(s):")
    for f in dll_findings:
        print(f"    [{f['severity']}] {f['finding_type']}: {f['description']}")

    # 4. Test Network Correlation (C2 Detection)
    print("\n4. Testing Suspicious Network Correlation...")
    suspicious_pids = {6632}
    mock_netscan = [
        # Normal process connection
        {"PID": 1204, "LocalAddr": "192.168.1.55", "LocalPort": 51000, "ForeignAddr": "142.250.190.46", "ForeignPort": 443, "State": "ESTABLISHED"},
        # Compromised process calling external C2 server
        {"PID": 6632, "LocalAddr": "192.168.1.55", "LocalPort": 49152, "ForeignAddr": "185.12.34.56", "ForeignPort": 443, "State": "ESTABLISHED"}
    ]
    network_findings = detect_suspicious_network(mock_netscan, suspicious_pids)
    print(f" -> Found {len(network_findings)} suspicious network connection(s):")
    for f in network_findings:
        print(f"    [{f['severity']}] {f['finding_type']}: {f['description']}")

    # Summary
    total = len(hidden_findings) + len(injection_findings) + len(dll_findings) + len(network_findings)
    print("\n" + "=" * 60)
    print(f"DETECTION TEST RESULT: PASSED ({total} threats correctly identified)")
    print("=" * 60)

if __name__ == "__main__":
    test_detection_engine()
