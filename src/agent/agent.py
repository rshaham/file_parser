import os
import subprocess
import json
import time
from typing import List, Dict, Optional

class AnalyzerWrapper:
    def __init__(self, analyzer_path: str):
        self.analyzer_path = analyzer_path

    def analyze(self, file_path: str) -> str:
        """Runs the C++ analyzer and returns the output as a string."""
        try:
            result = subprocess.run(
                [self.analyzer_path, file_path],
                capture_output=True,
                text=False,
                check=True
            )
            
            return result.stdout.decode('utf-8', errors='replace')
        except subprocess.CalledProcessError as e:
            print(f"Error running analyzer: {e}")
            return ""

import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class LLMClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.mock_mode = False
        
        if not self.api_key:
            print("Warning: No GEMINI_API_KEY found in environment. Using mock mode.")
            self.mock_mode = True
        else:
            try:
                genai.configure(api_key=self.api_key)
                #self.model = genai.GenerativeModel('gemini-3-pro-preview')
                self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
            except Exception as e:
                print(f"Failed to configure Gemini API: {e}. Falling back to mock.")
                self.mock_mode = True

    def query(self, prompt: str) -> str:
        """
        Queries the LLM (Gemini) or returns a mock response.
        """
        print(f"--- LLM Query ---\n{prompt[:200]}...\n-----------------")
        
        if self.mock_mode:
            # Mock response for SimpleMesh
            return """
struct SimpleMesh {
    uint32_t magic;
    uint32_t version;
    uint32_t v_count;
    uint32_t t_count;
    // Arrays would be handled by logic, but for this simple parser we just read header
};
"""

        try:
            # Enforce code-only output in the prompt if not already present
            system_instruction = """You are a C++ expert. 
            Your task is to write a COMPLETE C++ program that parses the given binary file format.
            
            Requirements:
            1. Define the necessary structs to read the file header.
            2. Implement a 'main' function that:
               - Accepts a filename as a command line argument.
               - Opens the file in binary mode.
               - Reads the header.
               - Prints ALL fields found in the header to stdout in the format:
                 FieldName: <value>
               
            Output ONLY valid C++ code. No markdown, no explanations.
            """
            full_prompt = f"{system_instruction}\n\n{prompt}"
            
            response = self.model.generate_content(full_prompt)
            text = response.text
            
            # Strip markdown code blocks if present
            if text.startswith("```"):
                lines = text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines)
                
            return text
        except Exception as e:
            print(f"LLM API Error: {e}")
            return ""

class ParserGenerator:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_cpp(self, code: str, filename: str = "generated_parser.cpp") -> str:
        """Saves the generated C++ code to a file."""
        path = os.path.join(self.output_dir, filename)
        with open(path, "w") as f:
            f.write(code)
        return path

    def compile_and_run(self, source_path: str, test_file: str) -> tuple[bool, str]:
        """Compiles the generated parser using CMake and runs it."""
        exe_path = source_path.replace(".cpp", ".exe")
        build_dir = os.path.join(self.output_dir, "build")
        os.makedirs(build_dir, exist_ok=True)
        
        # Create CMakeLists.txt
        cmake_content = f"""
cmake_minimum_required(VERSION 3.10)
project(GeneratedParser)
add_executable(parser "{os.path.basename(source_path)}")
"""
        with open(os.path.join(self.output_dir, "CMakeLists.txt"), "w") as f:
            f.write(cmake_content)
            
        # Build
        try:
            # Configure
            subprocess.run(["cmake", ".."], cwd=build_dir, check=True, capture_output=True)
            # Build
            subprocess.run(["cmake", "--build", "."], cwd=build_dir, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"CMake build failed: {e}")
            return False, ""
            
        # Find executable
        # It might be in build/Debug/parser.exe or build/parser.exe
        possible_paths = [
            os.path.join(build_dir, "Debug", "parser.exe"),
            os.path.join(build_dir, "parser.exe"),
            os.path.join(build_dir, "Release", "parser.exe")
        ]
        
        real_exe_path = None
        for p in possible_paths:
            if os.path.exists(p):
                real_exe_path = p
                break
                
        if not real_exe_path:
            print("Could not find built executable.")
            return False, ""

        # Run
        try:
            result = subprocess.run([real_exe_path, test_file], capture_output=True, text=False, check=True)
            output_text = result.stdout.decode('utf-8', errors='replace')
            print(f"Parser Output: {output_text}")
            return True, output_text
        except subprocess.CalledProcessError:
            return False, ""

import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.logger import ExperimentLogger

class Validator:
    def __init__(self):
        pass

    def validate(self, parser_output: str, ground_truth_spec: Dict, file_path: str) -> float:
        """
        Validates parser output against the ground truth spec.
        The spec tells us how to read the file to get the 'true' values.
        """
        # 1. Read the file using the spec to get true values
        truth = self._read_ground_truth(file_path, ground_truth_spec)
        
        # 2. Parse the agent's output
        parsed = {}
        for line in parser_output.splitlines():
            if ": " in line:
                key, val = line.split(": ")
                try:
                    # Handle float/int
                    if "." in val: parsed[key] = float(val)
                    else: parsed[key] = int(val)
                except ValueError:
                    pass
                    
        # 3. Compare
        score = 0
        total = 0
        
        # Compare Header Fields
        for field in ground_truth_spec["header"]:
            name = field["name"]
            # The agent might name it differently, but for MVP we check if the VALUE exists in the output
            # Or we can try to match by name if the agent is good.
            # For now, let's look for exact value matches in the output? 
            # No, that's risky.
            
            # Better approach: The agent defines the struct. 
            # We can't easily map AgentField -> TrueField without more logic.
            # Simplified Validation: Check if the Agent printed the correct values for the header fields.
            
            true_val = truth.get(name)
            if true_val is not None:
                total += 1
                # Check if this value appears in the parsed output associated with ANY key
                # This is a loose check, but fair for "unknown" formats where names are guessed.
                match = False
                for k, v in parsed.items():
                    # approximate match for floats
                    if isinstance(v, float) and isinstance(true_val, float):
                        if abs(v - true_val) < 0.001: match = True
                    elif v == true_val:
                        match = True
                
                if match: score += 1
                
        return score / total if total > 0 else 0.0

    def _read_ground_truth(self, file_path: str, spec: Dict) -> Dict:
        import struct
        values = {}
        with open(file_path, 'rb') as f:
            # Read Header
            for field in spec["header"]:
                if field["type"] == "uint32":
                    val = struct.unpack('<I', f.read(4))[0]
                elif field["type"] == "uint16":
                    val = struct.unpack('<H', f.read(2))[0]
                elif field["type"] == "float":
                    val = struct.unpack('<f', f.read(4))[0]
                values[field["name"]] = val
        return values

class Agent:
    def __init__(self, analyzer_path: str, work_dir: str):
        self.analyzer = AnalyzerWrapper(analyzer_path)
        self.llm = LLMClient()
        self.generator = ParserGenerator(os.path.join(work_dir, "generated"))
        self.validator = Validator()
        self.logger = ExperimentLogger(os.path.join(work_dir, "logs"))
        self.work_dir = work_dir
        self.knowledge_base = []

    def run_experiment(self, format_name: str, spec_path: str, test_files: List[str]):
        """Runs an experiment on a specific format."""
        print(f"Starting experiment for {format_name}")
        
        # Load ground truth spec (HIDDEN from LLM)
        with open(spec_path, 'r') as f:
            spec = json.load(f)
            
        for file in test_files:
            print(f"Processing {file}...")
            
            # 1. Analyze
            analysis = self.analyzer.analyze(file)
            
            # 2. Reason
            prompt = f"Analyze this file format based on the following analysis:\n{analysis}\nPrevious knowledge: {self.knowledge_base}"
            hypothesis = self.llm.query(prompt)
            
            # 3. Generate Code
            source_path = self.generator.generate_cpp(hypothesis)
            
            # 4. Test
            success, output = self.generator.compile_and_run(source_path, file)
            
            score = 0.0
            if success:
                # 5. Validate
                score = self.validator.validate(output, spec, file)
                print(f"Validation Score: {score:.2f}")
                
                if score > 0.8:
                    self.knowledge_base.append(hypothesis)
            
            # 6. Log
            self.logger.log_attempt(
                file_path=file,
                analysis_summary=analysis[:200] + "...", # truncate
                prompt=prompt,
                hypothesis=hypothesis,
                generated_code=hypothesis, # approximate
                parser_output=output,
                validation_score=score,
                ground_truth=spec,
                success=success
            )

if __name__ == "__main__":
    # Default behavior for backward compatibility or simple testing
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    analyzer_path = os.path.join(base_dir, "src", "cpp_analyzer", "bin", "analyzer.exe")
    if not os.path.exists(analyzer_path):
         analyzer_path = os.path.join(base_dir, "src", "cpp_analyzer", "build", "Debug", "analyzer.exe")
    
    # Just print usage
    print("Please use 'src/experiments/experiment_runner.py' to run experiments.")
    print("Example: python src/experiments/experiment_runner.py --mode random --count 1")
