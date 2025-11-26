# LLM Agent File Format Reverse Engineering

This project explores the sample efficiency of LLM agents in reverse engineering unknown binary file formats.

## Project Structure

- `data/`: Generated test files (`SimpleMesh` format).
- `src/cpp_analyzer/`: C++ tool for entropy, alignment, and differential analysis.
- `src/experiments/`: Experiment runner and logs.
- `src/agent/`: Python agent library (orchestrates analysis and LLM).
- `src/baseline/`: Heuristic-based analyzer for comparison.
- `src/generator/`: Scripts to generate synthetic test data.

## Prerequisites

- Python 3.8+
- CMake 3.10+
- C++ Compiler (MSVC or GCC)
- Google Gemini API Key

## Setup

1.  **Install Python Dependencies**:
    ```bash
    pip install google-generativeai python-dotenv
    ```

2.  **Build C++ Analyzer**:
    ```bash
    cd src/cpp_analyzer
    mkdir build
    cd build
    cmake ..
    cmake --build .
    ```

3.  **Generate Data** (Optional, data already generated):
    ```bash
    python src/generator/generate_simplemesh.py
    ```

4.  **Configure Environment**:
    Copy `.env.example` to `.env` and set your API key:
    ```bash
    cp .env.example .env
    # Edit .env and add your GEMINI_API_KEY
    ```

## Usage

### Running Experiments

Use the `experiment_runner.py` script to run experiments.

**1. Random Format Experiment (Phase 2)**
Generates random binary formats ("unknowns") and tests the agent's ability to reverse engineer them.

```bash
python src/experiments/experiment_runner.py --mode random --count 1
```
- `--count`: Number of different random formats to generate and test.

**2. Existing Format Experiment**
Run on existing files (e.g., the `SimpleMesh` data generated in Setup).

```bash
python src/experiments/experiment_runner.py --mode existing --data_dir data
```

### Generating Random Formats

To test generalization, you can generate synthetic "unknown" formats standalone:

```bash
python src/generator/random_generator.py
```

### Experiment Logs

Results are logged to `experiments/logs/` in JSONL format. Each entry contains:
- `analysis_summary`: C++ analysis output.
- `hypothesis`: The LLM's reasoning.
- `generated_code`: The C++ parser code.
- `validation_score`: Accuracy against the ground truth spec.

### Running the Baseline

Run the heuristic comparison:
```bash
python src/baseline/baseline.py
```

## Research Goal

To measure how many files an LLM agent needs to correctly reverse engineer a format compared to traditional heuristics.
Current MVP results show the Agent achieving 100% accuracy on the `SimpleMesh` format, while the baseline heuristic achieved 27.5%.
