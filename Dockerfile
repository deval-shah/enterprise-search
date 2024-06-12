# Start with an NVIDIA CUDA base image that includes cuDNN
FROM nvidia/cuda:12.0.1-cudnn8-runtime-ubuntu22.04

# Install Python and pip
RUN apt-get update && \
    apt-get install -y python3-pip python3-dev curl vim git && \
    if [ ! -f /usr/bin/python ]; then ln -s /usr/bin/python3 /usr/bin/python; fi && \
    if [ ! -f /usr/bin/pip ]; then ln -s /usr/bin/pip3 /usr/bin/pip; fi && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
COPY install.sh /app/install.sh
ENV PATH=/usr/local/cuda/bin:$PATH
ENV CUDAToolkit_ROOT=/usr/local/cuda
ENV PYTHONPATH="${PYTHONPATH}:/app/llamasearch"
RUN pip install --upgrade pip && pip install -r requirements.txt && pip install git+https://github.com/FlagOpen/FlagEmbedding.git

COPY llamasearch/*py /app/llamasearch/
COPY model_files/*.gbnf /app/model_files/
COPY config.yaml /app/
COPY eval_metrics_config.yaml /app/

# Make port 8000 available to the world outside this container
EXPOSE 8000
ENV NAME es

# Copy the entrypoint script and the update the permissions
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]