
# Enterprise Search

Enterprise Search is a scalable Retrieval-Augmented Generation (RAG) pipeline designed to provide accurate answers based on your documents. It offers a simple, accessible API for indexing and querying over document collections, making it ideal for businesses and developers seeking efficient and local question-answering solutions.

## Core Features

- **Document Processing**: Efficiently handle various document formats including PDF, DOCX, and TXT files.
- **Semantic Embedding**: Utilize open source state-of-the-art embedding models to capture the meaning of your documents.
- **Vector Indexing**: Fast and scalable indexing of document vectors using Qdrant.
- **Hybrid Search**: Combine dense and sparse vector search using Reciprocal Rank Fusion (RRF) for improved retrieval accuracy.
- **LLM-powered Generation**: Generate contextually relevant answers using advanced language models.
- **Customizable Pipeline**: Easily configure and extend the pipeline to suit your specific needs.
- **RESTful API**: Simple API endpoints for document indexing, querying, and management.
- **Multi-tenancy Support**: Securely handle multiple users or organizations within the same instance.
- **Containerized Deployment**: Docker and Kubernetes support for easy scaling and deployment.

## Prerequisites

Before setting up Enterprise Search, ensure you have the following:

- Python 3.9 or higher
- Docker and Docker Compose
- CUDA 11 or higher (for GPU acceleration)
- Access to a vector database (Qdrant)
- Access to a document store and cache (Redis)
- Any specific API keys or accounts needed, e.g., OpenAI API key if using OpenAI models

## Tech Stack

- LlamaIndex (Document processing and indexing)
- Qdrant (Vector database)
- Redis (Caching and document storage)
- Ollama or OpenAI (Language models)
- FastAPI (API framework)
- Docker and Docker Compose
- Kubernetes (for deployment)
- Firebase (for authentication)
- pytest (for testing)
- DVC (for data version control)

## Local Setup

Set up a Conda environment locally:
```bash
conda create --name es_env python=3.9
conda activate es_env
pip install -r requirements.txt
```

## Configuration

1. Rename `.env.example` to `.env` and update the values to match your setup.

2. Update the configuration in `config/config.dev.yaml`. Default settings are defined in `llamasearch/settings.py`:
- `application`: General application settings
- `vector_store_config`: Qdrant settings for vector storage
- `qdrant_client_config`: Qdrant client connection settings
- `redis_config`: Redis settings for document store and cache
- `embedding`: Embedding model configuration (uses model from HuggingFace)
- `llm`: Language model configuration (uses model from ollama/openai)
- `reranker`: Reranker model settings (uses model from HuggingFace)

3. Setup up LLM of your choice.

### Open-Source Option: Ollama

1. **Start Ollama docker:**: Use the `docker/docker-compose-ollama.yml` file to run Ollama:
```bash
docker-compose -f docker/docker-compose-ollama.yml up -d
```
The docker container will pull models mentioned in the `config/config.dev.yaml` on startup. It may take few minutes to download the models. Check ollama docker logs for progress.

### External Providers Option: OpenAI

To use OpenAI's proprietary models, set `OPENAI_API_KEY` in .env file.

1. **Set up OpenAI API key**: Export your OpenAI API key:
```bash
export OPENAI_API_KEY=your_api_key_here
```
2. **Configure for OpenAI:**: Update the `config/config.dev.yaml` file to use an OpenAI model, set `use_openai` flag to `True`. Check the [openai models list](https://platform.openai.com/docs/models).

## Usage

### Running the Pipeline locally

1. Start the redis and qdrant services:
```bash
docker-compose -f docker/docker-compose.yml up -d redis qdrant
```

2. **Run the ES pipeline:**:
```bash
python -m llamasearch.pipeline
```

The pipeline loads documents from `application->data_path` defined in config file, processes and indexes them on startup.

3. Enter your query when prompted. Results will be displayed in the terminal.

## API

We provide a RESTful API for document indexing, querying, and management. Follow steps to test the pipeline and backend server (API) using curl locally.

Default API settings are defined in `llamasearch/api/core/config.py`. These settings can be customized using environment variables defined in `.env` file in the project root.

*Important: When deploying to production, ensure you set appropriate values related to server, authentication.*

1. **Build the Docker Image:**
Run the following command to build the Docker image.
```bash
docker build -t es:latest -f docker/Dockerfile .
```

2. **Authentication**:  Update `FIREBASE_CREDENTIALS_PATH` to point to your firebase credentials file in `.env` file for user authentication. Refer to [Firebase README](docs/firebase.md) for instructions.

*Note: Currently, we only support testing API endpoints with authentication enabled. A firebase account is required to test the API endpoints.*

3. **Setup LLM**: Setup the LLM of your choice (if you haven't already) as mentioned in the [configuration](#configuration) section.

4. **Run the docker image:**
Adjust docker mount points in the `docker/docker-compose.yml` file to point to match your local setup. It will run the API server on port 8010 by default.
```bash
docker-compose -f docker/docker-compose.yml up -d
```

For detailed API usage examples, including request and response formats, curl request examples and more, please refer to our [API Documentation](docs/curl.md).

## Testing

We use pytest for testing. To run the test suite:

1. Ensure you're in the project root directory.

2. Start the API server as stated in the [API](#api) section.

3. In another terminal, set up the Python path:
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

4. Run the tests:
```bash
dvc repro -f tests/dvc.yaml
```
For more detailed testing instructions, including how to run specific tests, please refer to our [Testing Guide](docs/testing.md).

## Deployment

Enterprise Search can be deployed using Kubernetes and Helm. Here's a high-level overview of the deployment process:

1. Build and push the Docker image to your docker registry:
```bash
docker build -t es:latest .
docker push es:latest
```

2. Configure your Kubernetes cluster and ensure `kubectl` is set up correctly.

3. Update the `k8s/values.yaml` file with your specific configuration.

4. Deploy using Helm:
```bash
cd k8s/
helm install enterprise-search . --values values.yaml
```

5. Monitor the deployment:
```bash
kubectl get pods,svc -n {{YOUR_NAMESPACE}}
```

For detailed deployment instructions, please refer to our [Deployment Guide](k8s/README.md).

## Contributing

## License

This project is licensed under the {{LICENSE_TYPE}} - see the [LICENSE]({{LICENSE_FILE_URL}}) file for details.

## Acknowledgements

Enterprise Search project is built upon valuable open source projects. We'd like to acknowledge the following projects and their contributors:

- [LlamaIndex](https://github.com/jerryjliu/llama_index) for a stable foundation for indexing and querying capabilities with wide array of integrations
- [Qdrant](https://github.com/qdrant/qdrant) for the vector database functionality
- [FastAPI](https://github.com/tiangolo/fastapi) for the high-performance web framework
- [Ollama](https://github.com/ollama/ollama) for local LLM inference
- [Redis](https://github.com/redis/redis) for caching and document storage
- [Docker](https://github.com/docker) and [Kubernetes](https://github.com/kubernetes/kubernetes) for containerization and orchestration

