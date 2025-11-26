#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <string>
#include <vector>

// Basic Analysis Structures
struct AnalysisResult {
  std::string filename;
  size_t fileSize;
  std::vector<uint8_t> rawData;       // Store raw data for analysis
  std::vector<float> entropyMap;      // Entropy per 64-byte chunk
  std::map<int, int> alignmentScores; // Alignment -> Score
};

// Helper: Calculate Shannon Entropy of a buffer
//
// Shannon Entropy measures the randomness or information density of data.
// Formula: H(X) = -sum(p(x) * log2(p(x)))
// Range: 0.0 (all bytes are same) to 8.0 (all bytes are random/uniform)
//
// Interpretation for Reverse Engineering:
// - Low Entropy (< 3.0): Text, padding (zeros), or sparse data.
// - Medium Entropy (3.0 - 6.0): Code, structured data, or repeating patterns.
// - High Entropy (> 7.0): Compressed data, encrypted data, or dense
// floating-point arrays.
//
// We calculate this per 64-byte chunk to visualize the "texture" of the file.
// For example, a file might start with low entropy (header) and switch to high
// entropy (mesh data).
float calculateEntropy(const std::vector<uint8_t> &data) {
  if (data.empty())
    return 0.0f;

  std::map<uint8_t, int> frequencies;
  for (uint8_t byte : data) {
    frequencies[byte]++;
  }

  float entropy = 0.0f;
  float total = static_cast<float>(data.size());

  for (auto const &[byte, count] : frequencies) {
    float p = count / total;
    entropy -= p * std::log2(p);
  }

  return entropy;
}

// Helper: Check alignment
//
// Detects if data is aligned to 2, 4, or 8 byte boundaries.
// This is crucial for identifying arrays of integers or floats.
//
// Heuristic:
// We iterate through the file at the given stride (e.g., 4 bytes).
// If the values interpreted at these offsets look like "small integers"
// (indices, counts), we increment the score. A high score suggests a structured
// array.
void checkAlignment(const std::vector<uint8_t> &data, AnalysisResult &result) {
  std::vector<int> alignments = {2, 4, 8};

  for (int align : alignments) {
    int score = 0;
    // Check if data looks aligned at these boundaries
    // Heuristic: Count how many values are "small integers" (likely
    // counts/indices) or "valid floats" when interpreted at this alignment. For
    // MVP, let's just check if 4-byte integers are small (< 100000)

    if (align == 4 && data.size() >= 4) {
      for (size_t i = 0; i <= data.size() - 4; i += 4) {
        // Safe cast? strict aliasing might be an issue but for MVP C++ char* is
        // usually fine
        uint32_t val = 0;
        // Manual reconstruction to avoid alignment issues on some archs (x86 is
        // fine though)
        val |= data[i];
        val |= (uint32_t)data[i + 1] << 8;
        val |= (uint32_t)data[i + 2] << 16;
        val |= (uint32_t)data[i + 3] << 24;

        if (val < 100000)
          score++;
      }
    }
    result.alignmentScores[align] = score;
  }
}

// Helper: Find repeating patterns
void findPatterns(const std::vector<uint8_t> &data, AnalysisResult &result) {
  // MVP: Just look for 4-byte sequences that repeat often
  // Placeholder for now
}

AnalysisResult analyzeFile(const std::string &filepath) {
  AnalysisResult result;
  result.filename = filepath;

  std::ifstream file(filepath, std::ios::binary);
  if (!file) {
    std::cerr << "Failed to open file: " << filepath << std::endl;
    return result;
  }

  // Read entire file
  std::vector<uint8_t> buffer((std::istreambuf_iterator<char>(file)),
                              std::istreambuf_iterator<char>());
  result.rawData = buffer;
  result.fileSize = buffer.size();

  // Calculate Entropy Map (64-byte chunks)
  const size_t chunkSize = 64;
  for (size_t i = 0; i < buffer.size(); i += chunkSize) {
    size_t end = std::min(i + chunkSize, buffer.size());
    std::vector<uint8_t> chunk(buffer.begin() + i, buffer.begin() + end);
    result.entropyMap.push_back(calculateEntropy(chunk));
  }

  // Check Alignment
  checkAlignment(result.rawData, result);

  return result;
}

void printAnalysis(const AnalysisResult &result) {
  std::cout << "File: " << result.filename << std::endl;
  std::cout << "Size: " << result.fileSize << " bytes" << std::endl;

  std::cout << "Alignment Scores: ";
  for (auto const &[align, score] : result.alignmentScores) {
    std::cout << align << ":" << score << " ";
  }
  std::cout << std::endl;

  std::cout << "Entropy Map (" << result.entropyMap.size()
            << " chunks):" << std::endl;

  // Simple visualization
  for (size_t i = 0; i < result.entropyMap.size(); ++i) {
    float e = result.entropyMap[i];
    // Scale 0-8 to 0-10 chars
    int bars = static_cast<int>(e * 1.25f);
    std::cout << std::setw(4) << (i * 64) << ": [" << std::string(bars, '#')
              << std::string(10 - bars, ' ') << "] " << std::fixed
              << std::setprecision(2) << e << std::endl;
  }
}

// Helper: Differential Analysis
//
// Compares two files to identify structural differences.
// Currently, we only compare file sizes to detect "strides".
//
// Usage:
// If File A has 10 items and File B has 20 items, and Size(B) - Size(A) = 120
// bytes, then we can infer that each item is likely 12 bytes (120 / 10).
void compareFiles(const AnalysisResult &r1, const AnalysisResult &r2) {
  std::cout << "\nDifferential Analysis (" << r1.filename << " vs "
            << r2.filename << "):" << std::endl;

  if (r1.fileSize != r2.fileSize) {
    std::cout << "Size diff: " << r1.fileSize << " vs " << r2.fileSize
              << " (Delta: " << (long long)r2.fileSize - (long long)r1.fileSize
              << ")" << std::endl;
  } else {
    std::cout << "Size match." << std::endl;
  }
}

int main(int argc, char *argv[]) {
  if (argc < 2) {
    std::cerr << "Usage: analyzer <file_path> [compare_file_path]" << std::endl;
    return 1;
  }

  std::string filepath = argv[1];
  AnalysisResult result = analyzeFile(filepath);
  printAnalysis(result);

  if (argc >= 3) {
    std::string filepath2 = argv[2];
    AnalysisResult result2 = analyzeFile(filepath2);
    compareFiles(result, result2);
  }

  return 0;
}
