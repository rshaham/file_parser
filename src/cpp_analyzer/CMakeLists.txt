cmake_minimum_required(VERSION 3.10)
project(FormatAnalyzer)

set(CMAKE_CXX_STANDARD 17)

# Source files
file(GLOB SOURCES "src/*.cpp")

# Executable
add_executable(analyzer ${SOURCES})

# Output directory
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/bin)
