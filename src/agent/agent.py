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
                text=True,
                check=True
            )
            return result.stdout
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
               - Prints the following fields to stdout in this EXACT format:
                 Magic: <integer value>
                 Version: <integer value>
                 Vertices: <integer value>
                 Triangles: <integer value>
            
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
            result = subprocess.run([real_exe_path, test_file], capture_output=True, text=True, check=True)
            print(f"Parser Output: {result.stdout}")
            return True, result.stdout
        except subprocess.CalledProcessError:
            return False, ""

class Validator:
    def __init__(self):
        pass

    def get_ground_truth(self, file_path: str) -> Dict:
        """Reads the file using the known spec to get ground truth."""
        import struct
        with open(file_path, 'rb') as f:
            magic = f.read(4)
            version = struct.unpack('<I', f.read(4))[0]
            v_count = struct.unpack('<I', f.read(4))[0]
            t_count = struct.unpack('<I', f.read(4))[0]
            return {
                "magic": int.from_bytes(magic, byteorder='little'), # C++ prints int
                "version": version,
                "v_count": v_count,
                "t_count": t_count
            }

    def validate(self, parser_output: str, file_path: str) -> float:
        """Compares parser output to ground truth. Returns accuracy score (0.0-1.0)."""
        truth = self.get_ground_truth(file_path)
        
        # Parse output
        # Expected format: "Key: Value"
        parsed = {}
        for line in parser_output.splitlines():
            if ": " in line:
                key, val = line.split(": ")
                try:
                    parsed[key] = int(val)
                except ValueError:
                    pass
        
        # Compare
        score = 0
        total = 4 # Magic, Version, Vertices, Triangles
        
        if parsed.get("Magic") == truth["magic"]: score += 1
        if parsed.get("Version") == truth["version"]: score += 1
        if parsed.get("Vertices") == truth["v_count"]: score += 1
        if parsed.get("Triangles") == truth["t_count"]: score += 1
        
        return score / total

class Agent:
    def __init__(self, analyzer_path: str, work_dir: str):
        self.analyzer = AnalyzerWrapper(analyzer_path)
        self.llm = LLMClient()
        self.generator = ParserGenerator(os.path.join(work_dir, "generated"))
        self.validator = Validator()
        self.work_dir = work_dir
        self.knowledge_base = []

    def run_loop(self, test_files: List[str]):
        for file in test_files:
            print(f"Processing {file}...")
            
            # 1. Analyze
            analysis = self.analyzer.analyze(file)
            print(f"Analysis complete. Entropy map size: {len(analysis)}")
            
            # 2. Reason (Hypothesis)
            prompt = f"Analyze this file format based on the following analysis:\n{analysis}\nPrevious knowledge: {self.knowledge_base}"
            hypothesis = self.llm.query(prompt)
            
            # 3. Generate Code
            source_path = self.generator.generate_cpp(hypothesis)
            
            # 4. Test
            success, output = self.generator.compile_and_run(source_path, file)
            
            if success:
                print("Parser ran successfully.")
                # 5. Validate
                accuracy = self.validator.validate(output, file)
                print(f"Validation Accuracy: {accuracy * 100:.1f}%")
                
                if accuracy > 0.8:
                    print("High confidence! Adding to knowledge base.")
                    self.knowledge_base.append(hypothesis)
            else:
                print("Failure. Parser crashed or failed.")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    analyzer_path = os.path.join(base_dir, "src", "cpp_analyzer", "bin", "analyzer.exe")
    # Check if Debug/Release path
    if not os.path.exists(analyzer_path):
         analyzer_path = os.path.join(base_dir, "src", "cpp_analyzer", "build", "Debug", "analyzer.exe")
         
    data_dir = os.path.join(base_dir, "data")
    test_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(".smsh")]
    
    agent = Agent(analyzer_path, os.path.join(base_dir, "experiments"))
    agent.run_loop(test_files[:1]) # Test with just 1 file for now

if __name__ == "__main__":
    main()
