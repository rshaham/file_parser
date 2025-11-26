import json
import time
import os
from typing import Dict, Any, Optional

class ExperimentLogger:
    def __init__(self, log_dir: str = "experiments/logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.current_log_file = os.path.join(log_dir, f"experiment_{int(time.time())}.jsonl")

    def log_attempt(self, 
                    file_path: str, 
                    analysis_summary: str,
                    prompt: str,
                    hypothesis: str,
                    generated_code: str,
                    parser_output: str,
                    validation_score: float,
                    ground_truth: Optional[Dict] = None,
                    success: bool = False):
        
        entry = {
            "timestamp": time.time(),
            "file_path": file_path,
            "analysis_summary": analysis_summary,
            "prompt": prompt,
            "hypothesis": hypothesis,
            "generated_code": generated_code,
            "parser_output": parser_output,
            "validation_score": validation_score,
            "ground_truth": ground_truth,
            "success": success
        }
        
        with open(self.current_log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
            
    def log_error(self, file_path: str, error_msg: str):
        entry = {
            "timestamp": time.time(),
            "file_path": file_path,
            "error": error_msg,
            "success": False
        }
        with open(self.current_log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
