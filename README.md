# Enterprise Search

## Overview

The Enterprise Search project is intended to index and query documents efficiently using a combination of LLM and vector search database. It follows a It leverages the LLaMA index framework to process, embed, and index documents for semantic search. This project integrates Qdrant as a vector search engine and Redis for caching and document storage.

## Prerequisites

Before setting up the project, ensure you have the following installed:
- Python 3.8 or higher
- Docker and Docker Compose (for Qdrant and Redis)
- pip for Python package management

## Setup Instructions

### 1. Install Dependencies

Install the required Python dependencies using pip.

```bash
pip install -r requirements.txt
```

### 2. Setup Qdrant

Qdrant is used as the vector search database. Follow these steps to set it up using Docker.

- **Pull Qdrant Docker Image**

```bash
docker pull qdrant/qdrant
```

- **Run Qdrant Container**

```bash
docker run -d --name qdrant-vector-store -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

This command runs Qdrant vector store and exposes it on `http://localhost:6333`.

- **Create a collection Qdrant database**

```bash
curl -X PUT http://localhost:6333/collections/test   -H 'Content-Type: application/json' --data-raw '{"vectors": {"size": 384, "distance": "Cosine"} }'
```

This command sends a PUT request to the Qdrant server to create a new collection named test.

The vector_size should match the dimensionality of the vectors produced by your embedding model [local:BAAI/bge-small-en-v1.5](https://huggingface.co/BAAI/bge-small-en-v1.5) which is 384. 

The distance metric is set to Cosine, which is often used for semantic search applications, but you can choose another distance metric supported by Qdrant if it better suits your use case.

### 3. Setup Redis

Redis is used for caching and document storage. Setup Redis using Docker as follows.

- **Pull Redis Docker Image**

```bash
docker pull redis
```

- **Run Redis Container**

```bash
docker run --name ingestion-redis -p 6379:6379 -d redis
```

This command runs Redis and exposes it on `localhost` on port `6379`.

### 4. Install Ollama Model

1. **Install Ollama Engine**: Execute the installation script:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```
2. **Pull Mistral Model**: Download the model:
   ```bash
   ollama pull mistral:7b-instruct
   ```
3. **Explore More Models**: If you would like to change the open-source LLM models, please have a look at [Ollama Library](https://ollama.com/library) and pull the relevant model tag.

### 5. Update Configuration

Update `config.yml` with the correct paths and configurations for your setup. Here's an example configuration:

```yaml
data_path: "./data/test/"
qdrant_client_config:
  url: "http://localhost:6333"
  prefer_grpc: False
vector_store_config:
  collection_name: "test"
redis_config:
  host: "localhost"
  port: 6379
embed_model: "local:BAAI/bge-small-en-v1.5"
llm_model: "mistral"
```
- **data_path**: Directory containing documents to index.
- **qdrant_client_config**: Configuration for connecting to Qdrant.
- **vector_store_config**: Configuration for the vector store in Qdrant. The collection name should match with the one created above.
- **redis_config**: Configuration for connecting to Redis.
- **embed_model**: The embedding model for document processing.
- **llm_model**: The large language model name pulled using ollama.

### 6. Running the Application

Ensure you have uploaded documents into the `data_path` folder specified in your configuration and that both Qdrant and Redis dockers are running before attempting to run the application.

A sample test pdf is added in `./data/test/` for testing. Feel free to add other pdf, text, docx.. files for testing.

To run the streamlit application, navigate to the project directory and use the following command:

```bash
streamlit run app.py
```

For querying without the Streamlit interface, you can use:

```bash
python pipeline.py --query "your search query here"
```
To test the application and check its output, you can use the Streamlit interface or directly interact with the command line interface as mentioned above.

## Troubleshooting

- **Qdrant/Redis Connection Issues**: Ensure that Qdrant and Redis are running and accessible at the URLs and ports specified in `config.yml`.
- **Dependency Errors**: Make sure all Python dependencies are installed correctly as per `requirements.txt`.
- **Configuration Errors**: Verify that all paths and configurations in `config.yml` are correct and point to the right resources.
