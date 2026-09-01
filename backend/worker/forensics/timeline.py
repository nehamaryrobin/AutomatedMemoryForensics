import dateutil.parser
from datetime import datetime

def parse_vol_time(time_str):
    """Safely parses Volatility time strings to timezone-aware datetime objects."""
    if not time_str or time_str == "N/A" or time_str == "-":
        return None
    try:
        dt = dateutil.parser.parse(time_str)
        if dt.tzinfo is None:
            import datetime
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except:
        return None

def generate_timeline(plugin_outputs: dict) -> list:
    """
    Extracts chronological events from Volatility plugins (process starts, network connections).
    Returns a sorted list of dictionaries.
    """
    events = []
    
    pslist_data = plugin_outputs.get("windows.pslist.PsList", [])
    for proc in pslist_data:
        pid = proc.get("PID")
        name = proc.get("ImageFileName", "Unknown")
        
        # Process Creation
        create_time_str = proc.get("CreateTime")
        if create_time_str:
            dt = parse_vol_time(create_time_str)
            if dt:
                events.append({
                    "timestamp": dt,
                    "event_type": "PROCESS_START",
                    "details": f"Process started: {name} (PID: {pid})"
                })
                
        # Process Exit
        exit_time_str = proc.get("ExitTime")
        if exit_time_str:
            dt = parse_vol_time(exit_time_str)
            if dt:
                events.append({
                    "timestamp": dt,
                    "event_type": "PROCESS_EXIT",
                    "details": f"Process exited: {name} (PID: {pid})"
                })
                
    netscan_data = plugin_outputs.get("windows.netscan.NetScan", [])
    for net in netscan_data:
        pid = net.get("PID")
        create_time_str = net.get("Created")
        if create_time_str:
            dt = parse_vol_time(create_time_str)
            if dt:
                local = f"{net.get('LocalAddr')}:{net.get('LocalPort')}"
                remote = f"{net.get('ForeignAddr')}:{net.get('ForeignPort')}"
                events.append({
                    "timestamp": dt,
                    "event_type": "NETWORK_CONNECTION",
                    "details": f"Network socket created by PID {pid} (Local: {local}, Remote: {remote})"
                })
                
    # Sort events chronologically
    events.sort(key=lambda x: x["timestamp"])
    
    return events
