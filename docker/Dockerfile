# Start with an NVIDIA CUDA base image that includes cuDNN
FROM nvidia/cuda:12.0.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.9 and pip
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.9 python3.9-dev python3.9-distutils curl vim git build-essential gcc && \
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python3.9 get-pip.py && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.9 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1 && \
    rm get-pip.py && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
COPY docker/install.sh /app/
COPY docker/entrypoint.sh /app/

ENV PATH=/usr/local/cuda/bin:$PATH
ENV CUDAToolkit_ROOT=/usr/local/cuda
ENV PYTHONPATH="${PYTHONPATH}:/app/llamasearch"

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY llamasearch /app/llamasearch/
COPY config/*.yaml /app/config/

EXPOSE 8010
ENV NAME es
ENV PYTHONPATH="/app:${PYTHONPATH}"
ENV DOCKER_ENV=true

COPY docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
