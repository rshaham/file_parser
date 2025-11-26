import os
import struct
import math
from typing import List, Dict

class BaselineHeuristic:
    def __init__(self):
        pass

    def analyze_file(self, file_path: str) -> Dict:
        """
        Analyzes a file using heuristics to infer structure.
        Returns a dictionary with inferred fields.
        """
        with open(file_path, 'rb') as f:
            data = f.read()
            
        file_size = len(data)
        
        # Heuristic 1: Header detection
        # Assume first 4-16 bytes are header.
        # Look for "Magic" (ASCII)
        magic_candidate = data[:4]
        try:
            magic_str = magic_candidate.decode('ascii')
            if not magic_str.isalnum():
                magic_str = None
        except:
            magic_str = None
            
        # Heuristic 2: Count detection
        # Look for small integers in the header area that might match file size / record size
        # or just be small counts.
        candidates = []
        for i in range(4, 16, 4): # Check bytes 4-16
            if i + 4 <= len(data):
                val = struct.unpack('<I', data[i:i+4])[0]
                if val < 100000: # Reasonable count
                    candidates.append((i, val))
        
        # Heuristic 3: Structure Inference
        # If we have two counts C1, C2, check if FileSize ~= Header + C1*S1 + C2*S2
        # Try common sizes S = 12 (vec3), 4 (int), etc.
        
        inferred_structure = {}
        
        if magic_str:
            inferred_structure["Magic"] = int.from_bytes(magic_candidate, byteorder='little')
        
        # Try to fit C1 * 12 + C2 * 12 + HeaderSize == FileSize
        # This is specific to our Mesh hypothesis but "Baseline" implies some domain knowledge or generic fitting.
        # Let's try to find C1 and C2 such that:
        # 16 + C1*12 + C2*12 == FileSize
        
        found_fit = False
        if len(candidates) >= 2:
            c1 = candidates[0][1]
            c2 = candidates[1][1]
            
            # Check fit
            if 16 + c1 * 12 + c2 * 12 == file_size:
                inferred_structure["Version"] = 1 # Guess
                inferred_structure["Vertices"] = c1
                inferred_structure["Triangles"] = c2
                found_fit = True
            elif 16 + c1 * 12 + c2 * 4 == file_size: # Maybe triangles are 1 int? Unlikely for mesh
                 pass
        
        return inferred_structure

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(base_dir, "data")
    test_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(".smsh")]
    
    heuristic = BaselineHeuristic()
    
    print("Running Baseline Heuristic...")
    total_score = 0
    total_files = 0
    
    # We need the validator from agent.py or reimplement it
    # Let's just import it if possible, or copy-paste for independence
    import sys
    sys.path.append(os.path.join(base_dir, "src", "agent"))
    from agent import Validator
    validator = Validator()
    
    for file in test_files:
        print(f"Analyzing {os.path.basename(file)}...")
        result = heuristic.analyze_file(file)
        
        # Convert to "parser output" format for validator
        output_str = ""
        if "Magic" in result: output_str += f"Magic: {result['Magic']}\n"
        if "Version" in result: output_str += f"Version: {result.get('Version', 1)}\n"
        if "Vertices" in result: output_str += f"Vertices: {result['Vertices']}\n"
        if "Triangles" in result: output_str += f"Triangles: {result['Triangles']}\n"
        
        accuracy = validator.validate(output_str, file)
        print(f"  Inferred: {result}")
        print(f"  Accuracy: {accuracy * 100:.1f}%")
        
        total_score += accuracy
        total_files += 1
        
    print(f"Average Baseline Accuracy: {(total_score / total_files) * 100:.1f}%")

if __name__ == "__main__":
    main()
