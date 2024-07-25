#!/bin/bash
# Set environment variable required by llama-cpp-python for CUDA support
export CMAKE_ARGS="-DLLAMA_CUBLAS=on"

# Install the llama-cpp-python package
python -m pip install llama-cpp-python --prefer-binary --no-cache-dir --extra-index-url=https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu122