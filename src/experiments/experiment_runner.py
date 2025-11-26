import argparse
import os
import sys
import json
from typing import List

# Add src to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent.agent import Agent
from generator.random_generator import RandomFormatGenerator

def run_random_experiment(agent: Agent, count: int, output_dir: str):
    print(f"Running Random Experiment with {count} formats...")
    gen = RandomFormatGenerator(os.path.join(output_dir, "data", "random"))
    
    for i in range(count):
        format_name = f"RandomFormat_{i}"
        print(f"\n--- Generating {format_name} ---")
        spec = gen.generate_random_format(format_name, num_files=3)
        
        test_files = [os.path.join(output_dir, "data", "random", f"{format_name}_{j}.bin") for j in range(3)]
        spec_path = os.path.join(output_dir, "data", "random", f"{format_name}_spec.json")
        
        agent.run_experiment(format_name, spec_path, test_files)

def run_existing_experiment(agent: Agent, data_dir: str):
    print(f"Running Experiment on existing files in {data_dir}...")
    
    # Check for known specs
    spec_path = os.path.join(data_dir, "simplemesh_spec.json")
    if os.path.exists(spec_path):
        print(f"Found spec file: {spec_path}")
        test_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(".smsh")]
        agent.run_experiment("SimpleMesh", spec_path, test_files)
    else:
        print("Warning: Existing file validation requires a ground truth spec. Skipping validation for now.")
        test_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(".smsh")]
        # Run without validation (pass None/dummy path? Agent expects path)
        # We need to handle this in Agent.run_experiment or just create a dummy spec
        pass

def main():
    parser = argparse.ArgumentParser(description="Run LLM Reverse Engineering Experiments")
    parser.add_argument("--mode", choices=["random", "existing"], default="random", help="Experiment mode")
    parser.add_argument("--count", type=int, default=1, help="Number of random formats to generate")
    parser.add_argument("--data_dir", type=str, help="Directory for existing data")
    
    args = parser.parse_args()
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    analyzer_path = os.path.join(base_dir, "src", "cpp_analyzer", "bin", "analyzer.exe")
    if not os.path.exists(analyzer_path):
         analyzer_path = os.path.join(base_dir, "src", "cpp_analyzer", "build", "Debug", "analyzer.exe")
    
    experiments_dir = os.path.join(base_dir, "experiments")
    agent = Agent(analyzer_path, experiments_dir)
    
    if args.mode == "random":
        run_random_experiment(agent, args.count, experiments_dir)
    elif args.mode == "existing":
        if not args.data_dir:
            print("Error: --data_dir required for existing mode")
            return
        run_existing_experiment(agent, args.data_dir)

if __name__ == "__main__":
    main()
