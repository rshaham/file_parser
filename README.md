# LLM Agent File Format Reverse Engineering

This project explores the sample efficiency of LLM agents in reverse engineering unknown binary file formats.

## Project Structure

- `data/`: Generated test files (`SimpleMesh` format).
- `src/cpp_analyzer/`: C++ tool for entropy, alignment, and differential analysis.
- `src/agent/`: Python agent that orchestrates the analysis and uses an LLM to hypothesize structure.
- `src/baseline/`: Heuristic-based analyzer for comparison.
- `src/generator/`: Script to generate synthetic test data.

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

### Running the Agent

The agent analyzes files, queries Gemini for a hypothesis, generates a C++ parser, and validates it.

1.  Ensure `.env` is configured with your API Key.

2.  Run the Agent:
    ```bash
    python src/agent/agent.py
    ```

### Running the Baseline

Run the heuristic comparison:
```bash
python src/baseline/baseline.py
```

## Research Goal

To measure how many files an LLM agent needs to correctly reverse engineer a format compared to traditional heuristics.
Current MVP results show the Agent achieving 100% accuracy on the `SimpleMesh` format, while the baseline heuristic achieved 27.5%.
