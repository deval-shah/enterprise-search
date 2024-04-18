# Start with an NVIDIA CUDA base image that includes cuDNN
FROM nvidia/cuda:12.0.1-cudnn8-runtime-ubuntu22.04

# Install Python and pip
RUN apt-get update && \
    apt-get install -y python3-pip python3-dev curl vim && \
    if [ ! -f /usr/bin/python ]; then ln -s /usr/bin/python3 /usr/bin/python; fi && \
    if [ ! -f /usr/bin/pip ]; then ln -s /usr/bin/pip3 /usr/bin/pip; fi && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt
ENV PATH=/usr/local/cuda/bin:$PATH
ENV CUDAToolkit_ROOT=/usr/local/cuda
# Set the environment variable required by llama-cpp-python for CUDA support
ENV CMAKE_ARGS="-DLLAMA_CUBLAS=on"
RUN python -m pip install llama-cpp-python --prefer-binary --no-cache-dir --extra-index-url=https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu122
ENV PYTHONPATH="${PYTHONPATH}:/app/src"

COPY src/*py /app/src/
COPY model_files/*.gbnf /app/model_files/
COPY config.yaml /app/
COPY eval_metrics_config.yaml /app/

# Make port 8000 available to the world outside this container
EXPOSE 8000
ENV NAME es

# Copy the entrypoint script and the update the permissions
COPY entrypoint.sh /app/entrypoint.sh
COPY update_ollama_server_url_k8s.sh /app/update_ollama_server_url_k8s.sh
RUN chmod +x /app/entrypoint.sh /app/update_ollama_server_url_k8s.sh
ENTRYPOINT ["/app/entrypoint.sh"]
