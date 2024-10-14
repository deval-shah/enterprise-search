
# Enterprise Search

Enterprise Search offers foundation for building Retrieval-Augmented Generation (RAG) pipelines designed to provide accurate answers based on your documents. It offers a simple, accessible API for indexing and querying over document collections, making it ideal for businesses and developers seeking efficient and local question-answering solutions and deploying on their own infrastructure.

## 📚 Table of Contents

- [Prerequisites](#%EF%B8%8F-prerequisites)
- [Quick Start](#-quick-start)
- [Configuration](#%EF%B8%8F-configuration)
- [API](#-api)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Key Features](#-key-features)
- [License](#-license)
- [Acknowledgements](#-acknowledgements)

## 🛠️ Prerequisites

Before setting up Enterprise Search, ensure you have:

- Python 3.9 or higher
- Docker and Docker Compose
- CUDA 11 or higher (for GPU acceleration)

## ⚙️ Configuration

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

## 🚀 Quick Start

Refer the quick start notebook to test the pipeline:
  1. Open the `quick_start.ipynb` file in Jupyter Notebook or JupyterLab.
```bash
jupyter notebook quick_start.ipynb
```
  2. Follow the step-by-step instructions in the notebook to set up and test the pipeline.

Alternatively, you can use the command-line interface:

1. Set up the environment:
```bash
conda create --name es_env python=3.9
conda activate es_env
pip install -r requirements.txt
```

3. Configure the application
- Copy `.env.example` to `.env` and update the values as needed.
- Modify `config/config.dev.yaml` to suit your requirements.

4. Start the redis and qdrant services:
```bash
docker-compose -f docker/docker-compose.yml up -d redis qdrant
```

5. **Run the pipeline:**:
```bash
python -m llamasearch.pipeline
```

The pipeline loads documents from `application->data_path` defined in config file, processes and indexes them on startup. Enter your query when prompted. Results will be displayed in the terminal.

## 🌐 API

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

## 🧪 Testing

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

## 🚀 Deployment

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

## 🚀 Key Features

<table width=100%>
  <tr>
    <td width="50%">
      <strong><a href="#multi-document-query">Multi-Document Query Processing</a></strong><br/>
      Upload multiple documents (PDFs, DOCXs, CSVs) and ask questions spanning across them, leveraging comprehensive knowledge extraction.
      <br><br>
      <svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="docGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#4CAF50;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#45a049;stop-opacity:1" />
          </linearGradient>
        </defs>
        <rect x="10" y="10" width="60" height="80" rx="5" ry="5" fill="url(#docGradient)" />
        <rect x="20" y="20" width="40" height="5" fill="white" opacity="0.7" />
        <rect x="20" y="30" width="30" height="5" fill="white" opacity="0.7" />
        <circle cx="75" cy="75" r="20" fill="#2196F3" />
        <path d="M70 75 L80 75 M75 70 L75 80" stroke="white" stroke-width="3" />
      </svg>
    </td>
    <td width="50%">
      <strong><a href="#real-time-ingestion">Real-time Document Ingestion</a></strong><br/>
      Upload new documents during a query session, instantly incorporating fresh information into the knowledge base for immediate use.
      <br><br>
      <svg width="100" height="100" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="ingestGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#E91E63;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#d81b60;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect x="0" y="0" width="512" height="512" rx="50" ry="50" fill="url(#ingestGradient)" />
  <g transform="translate(56, 56) scale(0.78)" fill="white">
    <path d="M331.41 483.51v-239.2a7.347 7.347 0 0 0-2.01-3.78 7.224 7.224 0 0 0-5.11-2.15H187.75a7.338 7.338 0 0 0-7.26 7.26v236.47c0 1.91.77 3.75 2.15 5.08a6.81 6.81 0 0 0 4.96 2.15h136.82c1.92-.01 3.77-.79 5.11-2.15a7.775 7.775 0 0 0 1.98-3.82l-.1.14z" opacity="0.9"/>
    <path d="M250.45 222.77c-.5-.32-.97-.72-1.39-1.18l-16.04-17.37c-2.76-3.01-2.57-7.71.44-10.48 3.01-2.76 7.71-2.57 10.47.44l4.64 5.02v-31.26c0-4.1 3.33-7.43 7.43-7.43s7.43 3.33 7.43 7.43v32.7l5.36-4.47a7.404 7.404 0 0 1 10.42.96 7.392 7.392 0 0 1-.96 10.41l-18.29 15.26c-2.8 2.33-6.83 2.25-9.51-.03z" opacity="0.9"/>
  </g>
</svg>
    </td>
  </tr>
</table>
<table width="100%">
  <tr>
    <td width="50%"> 
      <strong><a href="#source-traceability">Source Traceability</a></strong><br/>
      For each response, get detailed information about which documents were used to generate the answer, ensuring transparency and verifiability.
      <br><br>
      <svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="traceGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#FF9800;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#F57C00;stop-opacity:1" />
          </linearGradient>
        </defs>
        <circle cx="50" cy="50" r="45" fill="url(#traceGradient)" />
        <path d="M30 70 Q50 20 70 70" fill="none" stroke="white" stroke-width="3" />
        <circle cx="50" cy="30" r="5" fill="white" />
        <circle cx="30" cy="70" r="5" fill="white" />
        <circle cx="70" cy="70" r="5" fill="white" />
      </svg>
    </td>
    <td width="50%">
      <strong><a href="#multi-tenant-support">Multi-Tenant Support</a></strong><br/>
      Handle multiple users with separate document collections, ensuring data isolation in the vector database for enhanced security and personalization.
      <br><br>
      <svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="tenantGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#9C27B0;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#7B1FA2;stop-opacity:1" />
          </linearGradient>
        </defs>
        <rect x="5" y="5" width="90" height="90" rx="10" ry="10" fill="url(#tenantGradient)" />
        <rect x="15" y="15" width="30" height="30" rx="5" ry="5" fill="white" opacity="0.7" />
        <rect x="55" y="15" width="30" height="30" rx="5" ry="5" fill="white" opacity="0.7" />
        <rect x="15" y="55" width="30" height="30" rx="5" ry="5" fill="white" opacity="0.7" />
        <rect x="55" y="55" width="30" height="30" rx="5" ry="5" fill="white" opacity="0.7" />
      </svg>
    </td>
  </tr>
</table>
<table width="100%">
  <tr>
    <td width="50%"> 
      <strong><a href="#evaluation-framework">Built-in Evaluation Framework</a></strong><br/>
      Assess and improve your RAG pipeline quality with comprehensive evaluation tools, ensuring optimal performance and accuracy.
      <br><br>
      <svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="evalGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#3F51B5;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#303F9F;stop-opacity:1" />
          </linearGradient>
        </defs>
        <rect x="5" y="5" width="100" height="90" rx="10" ry="10" fill="url(#evalGradient)" />
        <path d="M20 80 L20 40 L40 40 L40 80" fill="#8BC34A" />
        <path d="M45 80 L45 20 L65 20 L65 80" fill="#FFC107" />
        <path d="M70 80 L70 50 L90 50 L90 80" fill="#FF5722" />
        <path d="M10 30 L90 30" stroke="white" stroke-width="2" stroke-dasharray="5,5" />
      </svg>
    </td>
    <td width="50%">
      <strong><a href="#api-and-deployment">RESTful API and Deployment Support</a></strong><br/>
      Integrate easily with RESTful API endpoints and deploy effortlessly using included Kubernetes configurations for scalability.
      <br><br>
<svg width="100" height="100" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="apiGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#2196F3;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#1976D2;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect x="0" y="0" width="24" height="24" rx="5" ry="5" fill="url(#apiGradient)" />
  <g transform="translate(4, 4) scale(0.67)">
    <path d="M23,1 C23,1 16.471872,0.541707069 14,3 C13.9767216,3.03685748 10,7 10,7 L5,8 L2,10 L10,14 L14,22 L16,19 L17,14 C17,14 20.9631426,10.0232786 21,10 C23.4582929,7.5281282 23,1 23,1 Z" fill="none" stroke="white" stroke-width="1.5"/>
    <circle cx="16" cy="8" r="1.5" fill="white"/>
    <path d="M7,17 C6,16 4,16 3,17 C2,18 2,22 2,22 C2,22 6,22 7,21 C8,20 8,18 7,17 Z" fill="white" opacity="0.7"/>
  </g>
</svg>
    </td>
  </tr>
</table>

## 📄 License

This project is licensed under the *SOFTWARE LICENCE AGREEMENT* - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

Enterprise Search project is built on top of valuable open source projects. We'd like to acknowledge the following projects and their contributors:

- [LlamaIndex](https://github.com/jerryjliu/llama_index) for a stable foundation for RAG capabilities with wide array of integrations
- [Deepeval](https://github.com/confident-ai/deepeval) for the RAG evaluation framework
- [Qdrant](https://github.com/qdrant/qdrant) for the vector database functionality
- [FastAPI](https://github.com/tiangolo/fastapi) for the high-performance web framework
- [Ollama](https://github.com/ollama/ollama) for local LLM inference
- [Redis](https://github.com/redis/redis) for caching and document storage
- [Docker](https://github.com/docker) for containerization
- [Kubernetes](https://github.com/kubernetes/kubernetes) for orchestration

