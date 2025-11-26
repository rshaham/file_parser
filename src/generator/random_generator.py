import struct
import random
import os
import json
from typing import List, Dict, Any

class RandomFormatGenerator:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_random_format(self, name: str, num_files: int = 5) -> Dict[str, Any]:
        """
        Generates a random format specification and a set of files following it.
        Returns the 'Ground Truth' spec.
        """
        
        # 1. Define Random Schema
        has_magic = random.choice([True, False])
        magic_val = random.randint(0, 0xFFFFFFFF) if has_magic else None
        
        # Random fields in header
        header_fields = []
        if has_magic:
            header_fields.append({"name": "magic", "type": "uint32", "value": magic_val})
            
        # Add some random fixed fields (version, flags, etc)
        num_fixed = random.randint(1, 3)
        for i in range(num_fixed):
            header_fields.append({
                "name": f"field_{i}", 
                "type": random.choice(["uint32", "uint16", "float"]),
                "value": "random" # varies per file? or fixed? let's say fixed for version, random for others
            })
            
        # Add 1-2 arrays
        num_arrays = random.randint(1, 2)
        arrays = []
        for i in range(num_arrays):
            arrays.append({
                "name": f"array_{i}",
                "count_field": f"count_{i}", # We need to add this to header
                "type": random.choice(["float3", "uint32", "float"]),
                "stride": 0 # calculated later
            })
            # Add count to header
            header_fields.append({"name": f"count_{i}", "type": "uint32", "value": "variable"})

        spec = {
            "name": name,
            "header": header_fields,
            "arrays": arrays
        }
        
        # Save spec
        with open(os.path.join(self.output_dir, f"{name}_spec.json"), "w") as f:
            json.dump(spec, f, indent=2)
            
        # 2. Generate Files
        for i in range(num_files):
            self._write_file(os.path.join(self.output_dir, f"{name}_{i}.bin"), spec)
            
        return spec

    def _write_file(self, filepath: str, spec: Dict):
        with open(filepath, "wb") as f:
            # Track values for arrays
            counts = {}
            
            # Decide counts first
            for arr in spec["arrays"]:
                count = random.randint(5, 50)
                counts[arr["count_field"]] = count
                
            # Write Header
            for field in spec["header"]:
                val = 0
                if field["value"] == "variable":
                    # It's a count field
                    val = counts[field["name"]]
                elif field["value"] == "random":
                    if field["type"] == "float": val = random.random()
                    else: val = random.randint(0, 100)
                else:
                    val = field["value"]
                
                if field["type"] == "uint32": f.write(struct.pack('<I', int(val)))
                elif field["type"] == "uint16": f.write(struct.pack('<H', int(val)))
                elif field["type"] == "float": f.write(struct.pack('<f', float(val)))
                
            # Write Arrays
            for arr in spec["arrays"]:
                count = counts[arr["count_field"]]
                for _ in range(count):
                    if arr["type"] == "float3":
                        f.write(struct.pack('<fff', random.random(), random.random(), random.random()))
                    elif arr["type"] == "uint32":
                        f.write(struct.pack('<I', random.randint(0, 1000)))
                    elif arr["type"] == "float":
                        f.write(struct.pack('<f', random.random()))

def main():
    # Test
    gen = RandomFormatGenerator("data/random")
    spec = gen.generate_random_format("FormatA", 3)
    print(json.dumps(spec, indent=2))

if __name__ == "__main__":
    main()
