# Enterprise Search

## Overview

Enterprise search aims to give accurate answers on your documents.

The Enterprise Search pipeline is built using LLaMA index framework to process, embed, and index documents for semantic search and generate answers using indexed documents. We use Qdrant as a vector search engine (for indexing/retrieval of the document data) and Redis for document storage and caching.

## Prerequisites

Before setting up the project, ensure you have the following installed:
- Python 3.9 or higher
- Docker and Docker Compose
- Cuda 11 or higher

## Setup Instructions

### 1. Conda Setup (Local Testing)

**Set up a local Conda environment and install dependencies:**

Create and activate a new environment with Python 3.9:
```bash
conda create --name es_env python=3.9
conda activate es_env
pip install -r requirements.txt
```

### 2. Setup Qdrant

Qdrant is used as the vector search database to support efficient searching over vectorized data for retrieval. It is configured to run through `docker-compose.yml`:

This default configuration starts the Qdrant container on localhost on the ports 6333 and 6334.

### 3. Setup Redis

Redis serves as the caching and document storage layer. It is configured to run through `docker-compose.yml`:

This default configuration starts the Redis server accessible on port 6379 on localhost.

### 4. Setup LLM

The pipeline supports open source llms via Ollama and OpenAI models. Update the `config/config.dev.yaml` file to use the desired LLM.

#### Open-Source Option: Ollama

1. **Start Ollama docker:**: Use the `docker/docker-compose-ollama.yml` file to run Ollama:
   ```bash
   docker-compose -f docker/docker-compose-ollama.yml up -d
   ```
   The docker container will pull models mentioned in the `config/config.dev.yaml` on startup. It may take few minutes to download the models.
2. **Explore LLM Model library**: Please have a look at [Ollama Library](https://ollama.com/library) and pull the LLM model of your choice. Update the model name in the `config/config.dev.yaml`.

#### Closed-Source Option: OpenAI Models

Alternatively, you can use OpenAI's proprietary models, if you setup `OPENAI_API_KEY` then it will be used as default llm.

1. **Set up OpenAI API key**: Export your OpenAI API key:
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```
2. **Configure for OpenAI:**: Update the `config/config.dev.yaml` file to use an OpenAI model instead of a local Ollama model using `use_openai` flag. Check the [openai models list](https://platform.openai.com/docs/models).

### 5. Configuration Setup

Update the `config/config.dev.yaml` file with the necessary paths and configurations. The default config file assumes a localhost setup.

#### Configuration Descriptions:
- **application**: General application settings.
- **vector_store_config**: Qdrant is used as vector store for storing dense and sparse vectors for data retrieval.
- **qdrant_client_config**: Specifies the connection settings for Qdrant.
- **redis_config**: Redis is used for docstore and cache.
- **embedding**: Embedding model used for document processing. Pulled from HuggingFace library.
- **llm_model**: Generation model to generate response using context from retreival stage.
- **reranker**: Reranker model to refine the results post retrieval stage.

## Testing

### Before you start

1. **Update the config file**: Modify the [config](config/config.dev.yaml) file with the necessary data paths and configurations.
- A sample test PDF is provided in `./data/test/`.

2. **Rename the env file**: Rename the `.env.example` file to `.env` and update the config file path that matches your local setup. By default, it is set to [config](config/config.dev.yaml).

### Option 1: Testing the ES pipeline locally

1. **Run Qdrant and Redis services using docker-compose**: 
   ```bash
   docker-compose -f docker/docker-compose.yml up -d redis qdrant
   ```

2. **Setup LLM**: Refer to the [Setup LLM](#setup-llm) section above for instructions on setting up LLM for the pipeline.

3. **Run the ES pipeline:**:
   ```bash
   python -m llamasearch.pipeline
   ```
4. **Test**: The pipeline loads documents from `application->data_path` defined in config file, processes and indexes them. When prompted, enter your query. Results will be displayed in the terminal.

### Option 2: Testing the backend server (API) using curl locally 

1. **Build the Docker Image:**
   Open your terminal and run the following command to build the Docker image and run the docker image:
   ```bash
   docker build -t docker.aiml.team/products/aiml/enterprise-search/llamasearch:latest -f docker/Dockerfile .
   ```

2. **Authentication**:  Update `FIREBASE_CREDENTIALS_PATH` to point to your firebase credentials file in `.env` file for user authentication. [Step 4](#step-4)has instructions on how to setup firebase credentials.

3. **Run the docker image:**
   Adjust docker mount points in the `docker/docker-compose.yml` file to point to the local data path.
   ```bash
   docker-compose -f docker/docker-compose.yml up -d
   ```

4. **Test the API:**
For detailed instructions on how to test the API using curl, refer to the [curl.md](docs/curl.md) file.

### Option 3: Testing the UI and backend server locally

1. **Run the backend server**: Follow the steps 1-3 from [Option 2](#option-2)
2. **Run the UI**: Follow the [UI README](frontend/README.md) file to run the UI locally.s

## Unit Testing

Under maintainance

## Evaluation

- The [Eval README](docs/eval.md) file outlines the instructions on how to evaluate the ES pipeline.

## Deployment

- The [Deployment README](k8s/README.md) file outlines the instructions on how to deploy Enterprise Search on a cluster using Kubernetes and Helm.

## Release Notes

**Version 1.0.7 - 12/07/2024**
- Added support async support for faster ingestion
- Refractored the pipeline code to seperate vector search methods from pipeline code
- Added support for pipeline factory to manage simulatneous pipeline initializations and caching
- Added support for OpenAI models (embedding/generation)
- Added Ollama docker with auto pull of models defined in [config](config/config.dev.yaml)
- Restructured the code for easier maintainance