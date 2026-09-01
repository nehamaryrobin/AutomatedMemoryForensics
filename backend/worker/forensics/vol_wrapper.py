import subprocess
import json
import time
import os
import logging

logger = logging.getLogger(__name__)

class VolatilityWrapper:
    def __init__(self):
        # We assume the 'vol' command is available in the environment path 
        # because we installed volatility3 via pip in the worker's venv.
        self.vol_cmd = "vol"

    def run_plugin(self, dump_path: str, plugin_name: str, output_dir: str) -> dict:
        """
        Executes a Volatility 3 plugin via a subprocess and returns the parsed JSON result.
        Using subprocess prevents corrupt memory dumps from causing C-extension faults
        that could crash the entire Celery worker process.
        """
        start_time = time.time()
        
        # Make sure the output directory for this case exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Construct the command: vol -f <dump> -r json <plugin>
        cmd = [self.vol_cmd, "-f", dump_path, "-r", "json", plugin_name]
        
        result = {
            "plugin_name": plugin_name,
            "status": "FAILED",
            "execution_time": 0.0,
            "raw_output_path": None,
            "parsed_output": None,
            "error": None
        }

        try:
            # We capture stdout (JSON output) and stderr (Logs/Errors)
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=300) # 5 min timeout per plugin
            execution_time = time.time() - start_time
            result["execution_time"] = round(execution_time, 2)

            if process.returncode == 0:
                result["status"] = "SUCCESS"
                
                # Parse JSON output from stdout
                try:
                    parsed_json = json.loads(process.stdout)
                    
                    # Store the parsed JSON as a string for the DB (truncated if too large, or full)
                    # For safety, if it's massive, we might just store a summary, but for MVP we store it.
                    result["parsed_output"] = json.dumps(parsed_json)
                    
                    # Save the raw JSON to a file on disk
                    output_file_name = f"{plugin_name}.json"
                    output_file_path = os.path.join(output_dir, output_file_name)
                    
                    with open(output_file_path, "w") as f:
                        json.dump(parsed_json, f, indent=2)
                        
                    result["raw_output_path"] = output_file_path

                except json.JSONDecodeError:
                    result["status"] = "FAILED"
                    result["error"] = "Failed to parse JSON output from Volatility"
                    logger.error(f"JSON Parse Error on {plugin_name}:\n{process.stdout}")
            else:
                result["status"] = "FAILED"
                result["error"] = process.stderr
                logger.error(f"Volatility Execution Error on {plugin_name}:\n{process.stderr}")

        except subprocess.TimeoutExpired:
            result["status"] = "FAILED"
            result["error"] = "Plugin execution timed out after 300 seconds."
            logger.error(f"Timeout on {plugin_name}")
            
        except Exception as e:
            result["status"] = "FAILED"
            result["error"] = str(e)
            logger.error(f"Unexpected error on {plugin_name}: {e}")

        return result
