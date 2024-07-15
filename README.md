# Enterprise Search

## Overview

Enterprise search aims to give accurate answers on your documents.

The Enterprise Search pipeline is built using LLaMA index framework to process, embed, and index documents for semantic search and generate answers using indexed documents. We use Qdrant as a vector search engine (for indexing/retrieval of the document data) and Redis for document storage and caching.

## Prerequisites

Before setting up the project, ensure you have the following installed:
- Python 3.8 or higher
- Docker and Docker Compose
- Cuda 11 or higher

## Setup Instructions

### Option 1: Docker Setup (ES Backend server)

Ideal option if you are testing the API server or UI locally.

1. **Build the Docker Image:**
   Open your terminal and run the following command to build the Docker image and run the docker image using `docker-compose`:
   ```bash
   docker build -t docker.aiml.team/products/aiml/enterprise-search/llamasearch:latest -f docker/Dockerfile .
   ```

### Option 2: Conda Setup (Local Testing)

Ideal option if you are want to test/develop the pipeline

**Set up a local Conda environment and install dependencies:**

1. **Create a Conda Environment:**
   Create and activate a new environment with Python 3.9:
   ```bash
   conda create --name es_env python=3.9
   conda activate es_env
   pip install -r requirements.txt
   ```

### 2. Setup Qdrant

Qdrant is used as the vector search database to support efficient searching over vectorized data for retrieval. It is configured to run through `docker-compose.yml`:

```bash
docker-compose -f docker/docker-compose.yml up -d qdrant
```

This default configuration starts the Qdrant container on localhost on the ports 6333 and 6334.

### 3. Setup Redis

Redis serves as the caching and document storage layer. It is configured to run through `docker-compose.yml`:

```bash
docker-compose -f docker/docker-compose.yml up -d redis
```

This default configuration starts the Redis server accessible on port 6379 on localhost.

### 4. Setup LLM

The pipeline supports open source llms via Ollama and OpenAI models. Update the `config.yaml` file to use the desired LLM.

#### Open-Source Option: Ollama

1. **Start Ollama docker:**: Use the `docker-compose-ollama.yml` file to run Ollama:
   ```bash
   docker-compose -f docker/docker-compose-ollama.yml up -d
   ```
   The docker container will pull models mentioned in the config.yaml on startup. It may take few minutes to download the models. Start ES docker after the models are pulled.
2. **Explore LLM Model library**: Please have a look at [Ollama Library](https://ollama.com/library) and pull the LLM model of your choice. Update the model name in the `config.yaml`.

#### Closed-Source Option: OpenAI Models

Alternatively, you can use OpenAI's proprietary models, if you setup OPENAI_API_KEY then it will be used as default llm.

1. **Set up OpenAI API key**: Export your OpenAI API key:
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```
2. **Configure for OpenAI:**: Update the `config.yaml` file to use an OpenAI model instead of a local Ollama model. Check the [openai models list](https://platform.openai.com/docs/models).

### 5. Configuration Setup

Update the `config/config.dev.yaml` file with the necessary paths and configurations. The default config file assumes a localhost setup.

### Configuration Descriptions:
- **application**: General application settings.
- **vector_store_config**: Qdrant is used as vector store for storing dense and sparse vectors for data retrieval.
- **qdrant_client_config**: Specifies the connection settings for Qdrant.
- **redis_config**: Redis is used for docstore and cache.
- **embedding**: Embedding model used for document processing. Pulled from HuggingFace library.
- **llm_model**: Generation model to generate response using context from retreival stage.
- **reranker**: Reranker model to refine the results post retrieval stage.

### Test the Application

**Before you start:**
- Ensure there is atleast one document present in the `data_path` folder as defined in the `config/config.dev.yaml`.
- A sample test PDF is provided in `./data/test/`.

### Option 1: Testing the ES pipeline locally

### Option 2: Testing the backend server (API) using curl locally

### Option 3: Testing the UI and backend server locally

## Unit Testing

Under maintainance

## Evaluation

- The [Eval README](docs/eval.md) file outlines the instructions on how to evaluate the ES pipeline.

## Deployment

- The [README](k8s/README.md) file outlines the instructions on how to deploy Enterprise Search on a cluster using kubernetes and helm.

## Release Notes

**Version 1.0.7 - 12/07/2024**
- Added support async support for faster ingestion
- Refractored the pipeline code to seperate vector search methods from pipeline code
- Added support for pipeline factory to manage simulatneous pipeline initializations and caching
- Added support for OpenAI models (embedding/generation)
- Added Ollama docker with auto pull of models defined in config.yaml
- Restructured the code for easier maintainance