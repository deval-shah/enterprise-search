# Enterprise Search

## Overview

The Enterprise Search project is intended to index and query documents efficiently using a combination of LLM and vector search database. 

It leverages the LLaMA index framework to process, embed, and index documents for semantic search. We use Qdrant as a vector search engine (for indexing/retrieval of the document data) and Redis for document storage and caching.

## Prerequisites

Before setting up the project, ensure you have the following installed:
- Python 3.8 or higher
- Docker and Docker Compose (for Qdrant and Redis)

## Setup Instructions

You have two options to set up the Enterprise Search application: using Docker or Conda. Choose the method that best suits your development environment and preferences.

### Option 1: Docker Setup

**Build and run the Docker image for the Enterprise Search pipeline:**

1. **Build the Docker Image:**
   Open your terminal and run the following command to build the Docker image:
   ```bash
   docker build -t docker.aiml.team/products/aiml/enterprise-search/llamasearch:latest .
   ```

2. **Run the Docker Compose:**
   After building the image, use Docker Compose to start the services:
   ```bash
   docker-compose up
   ```
   **Note:** Ensure the Enterprise Search service declaration is active in the `docker-compose.yml`.

### Option 2: Conda Setup (Local Testing)

**Set up a local Conda environment and install dependencies:**

1. **Create a Conda Environment:**
   Use these commands to create and activate a new environment named `es_env` with Python 3.9:
   ```bash
   conda create --name es_env python=3.9
   conda activate es_env
   ```

2. **Install Dependencies:**
   Navigate to the directory containing your `requirements.txt` file, then install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

   **Important:** If you choose the Conda setup, ensure the Enterprise Search service declaration in the `docker-compose.yml` is commented out to avoid conflicts.

### 2. Setup Qdrant

Qdrant is utilized as the vector search database to support efficient searching over vectorized data. It is configured automatically through the provided `docker-compose.yml` setup.

Run the docker compose file to start `redis` and `qdrant` services.

```bash
docker-compose -f docker-compose.yml up
```

- **Docker Compose Configuration**:
  ```yaml
  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    restart: always
    environment:
      RUST_LOG: info
  ```
  This configuration starts a Qdrant container and makes it available on ports 6333 and 6334.

- **Create a Collection in Qdrant**:
  ```bash
  curl -X PUT http://localhost:6333/collections/test \
       -H 'Content-Type: application/json' \
       --data-raw '{"vectors": {"size": 384, "distance": "Cosine"}}'
  ```
  Run the above command to create a collection named `test` with vectors of size 384 using Cosine distance. Ensure this matches the vector dimensions produced by your configured embedding model in `config.yaml`.

### 3. Setup Redis

Redis serves as the caching and document storage layer. It is also configured to run through `docker-compose.yml`:

- **Docker Compose Configuration**:
  ```yaml
  redis:
    image: redis
    ports:
      - "6379:6379"
    restart: always
  ```
  This setup will start a Redis server accessible on port 6379 on localhost, managing data caching and session storage.

### 4. Install Ollama Model

1. **Install Ollama Engine**: Execute the installation script:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **Explore LLM Model library**: Please have a look at [Ollama Library](https://ollama.com/library) and pull the LLM model of your choice. Update the value in `config.yaml`.

3. **Pull LLM Model**: Command to download the LLM model:
   ```bash
   ollama pull mistral:7b-instruct
   ```

### 5. Configuration Setup

Update the `config.yaml` file with the necessary paths and configurations. The default config file assumes a local setup as per the docker compose.

```yaml
application:
  config_path: "config.yaml"
  data_path: "/data/files"
  log_dir: "/data/app/logs"
  upload_subdir: "uploads"

qdrant_client_config:
  url: "http://localhost:6333"
  prefer_grpc: False

vector_store_config:
  collection_name: "test"
  vector_size: 384
  distance: "Cosine"

redis_config:
  host: "localhost"
  port: 6379

embedding:
  embed_model: "local:BAAI/bge-small-en-v1.5"

llm:
  llm_model: "mistral:7b-instruct"
```

### Configuration Descriptions:
- **application**: General application settings including paths for data, logs, and uploads.
- **qdrant_client_config**: Specifies the connection settings for Qdrant, including the URL and whether to use gRPC.
- **vector_store_config**: Details about the vector store configuration in Qdrant, including collection name, vector size, and distance metric.
- **redis_config**: Configuration settings for Redis, specifying host and port.
- **embedding**: Configuration for the embedding model used for document processing. Pulled from HuggingFace library.
- **llm_model**: Llm used, indicating model name and version.

This configuration ensures all components of the system are appropriately directed and connected. Ensure that these values align with your actual deployment setup, particularly URLs and ports for services like Qdrant and Redis.

### Test the Application

**Before you start:**
- Ensure that documents are uploaded to the `data_path` folder as specified in your `config.yaml`. This folder should exist on your system and be accessible.
- A sample test PDF is provided in `./data/test/` for initial testing. You can also add other file types like text or DOCX files to this directory for further testing.

### Option 1: Using Streamlit Interface
1. **Open your terminal and navigate to the project directory.**
2. **Run the Streamlit application** by executing the following command:
   ```bash
   streamlit run src/streamlit-app.py
   ```
   This will start the Streamlit web interface, where you can interact with the application through a web browser.

### Option 2: Command Line Querying
1. **If you prefer to use the command line** (useful for automation or integration into other processes), you can query the application directly. Navigate to the project directory in your terminal.
2. **Execute a search query** by running:
   ```bash
   python -m llamasearch.pipeline --query "your search query here"
   ```
   Replace `"your search query here"` with your specific search terms.

## Kubernetes/Helm Deployment to the DPC cluster

- The [Eval README](docs/eval.md) file outlines the instructions on how to evaluate the ES pipeline.

## Kubernetes/Helm Deployment to the DPC cluster

- The [README](k8s/README.md) file outlines the instructions on how to deploy Enterprise Search on a cluster using kubernetes and helm.

## Troubleshooting

- **Qdrant/Redis Connection Issues**: Ensure that Qdrant and Redis are running and accessible at the URLs and ports specified in `config.yml`.
- **Dependency Errors**: Make sure all Python dependencies are installed correctly as per `requirements.txt`.
- **Configuration Errors**: Verify that all paths and configurations in `config.yml` and `eval_metrics_config.yml` are correct and point to the right resources.

## Release Notes

**Version 1.0.4 - 05/06/2024**
- Renamed src folder to llamasearch
- Updated the default model to 'llama3'
- Updated the user prompt template for the llama3 model
- Added reranker to improve retriever results
- Added citations support for query (Now we can see the doc id, text etc. that model used to generate)
- Added a flag to enable/disable services in k8s deployment values file. Added to avoid deploying all services during development.
- Simplified README, added docs folder