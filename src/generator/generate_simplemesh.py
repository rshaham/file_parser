import struct
import random
import os

def generate_simplemesh(filename, vertex_count, triangle_count):
    """
    Generates a SimpleMesh v1.0 binary file.
    
    Format:
    [0-3]   Magic: "SMSH"
    [4-7]   Version: uint32 = 1
    [8-11]  VertexCount: uint32
    [12-15] TriangleCount: uint32
    [16+]   Vertices: VertexCount * 12 bytes (3x float32)
    [?+]    Triangles: TriangleCount * 12 bytes (3x uint32)
    """
    
    magic = b'SMSH'
    version = 1
    
    with open(filename, 'wb') as f:
        # Header
        f.write(magic)
        f.write(struct.pack('<I', version))
        f.write(struct.pack('<I', vertex_count))
        f.write(struct.pack('<I', triangle_count))
        
        # Vertices
        for _ in range(vertex_count):
            x = random.uniform(-10.0, 10.0)
            y = random.uniform(-10.0, 10.0)
            z = random.uniform(-10.0, 10.0)
            f.write(struct.pack('<fff', x, y, z))
            
        # Triangles
        for _ in range(triangle_count):
            v0 = random.randint(0, vertex_count - 1)
            v1 = random.randint(0, vertex_count - 1)
            v2 = random.randint(0, vertex_count - 1)
            f.write(struct.pack('<III', v0, v1, v2))

def main():
    # Output to data directory relative to this script
    # src/generator/../../data
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../data")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate 10 files with different sizes
    configs = [
        (10, 5),
        (20, 10),
        (50, 30),
        (100, 50),
        (200, 100),
        (500, 200),
        (1000, 500),
        (5, 1),
        (15, 8),
        (25, 12)
    ]
    
    for i, (v_count, t_count) in enumerate(configs):
        filename = os.path.join(output_dir, f"test_{i:02d}.smsh")
        generate_simplemesh(filename, v_count, t_count)
        print(f"Generated {filename}: {v_count} vertices, {t_count} triangles")

if __name__ == "__main__":
    main()
