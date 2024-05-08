# Enterprise Search

## Overview

The Enterprise Search project is intended to index and query documents efficiently using a combination of LLM and vector search database. 
It follows a It leverages the LLaMA index framework to process, embed, and index documents for semantic search. This project integrates Qdrant as a vector search engine and Redis for caching and document storage.

## Prerequisites

Before setting up the project, ensure you have the following installed:
- Python 3.8 or higher
- Docker and Docker Compose (for Qdrant and Redis)

## Setup Instructions

### 1. Installation

**Building the Docker image for the ES pipeline:**

To build your Docker image from the Dockerfile:

```bash
docker build -t docker.aiml.team/products/aiml/enterprise-search/llamasearch:latest .
```

**Local Testing with Conda:**

If you prefer to test the application locally without Docker, set up a Conda environment and install the necessary dependencies:

- **Create and activate a new Conda environment:**

```bash
conda create --name es_env python=3.9
conda activate es_env
```

- **Install dependencies:**

Navigate to the directory containing your `requirements.txt` and run:

```bash
pip install -r requirements.txt
```

If you are not building the ES pipeline docker image, then comment the es service declaration in the `docker-compose.yml`.

### 2. Setup Qdrant

Qdrant is utilized as the vector search database to support efficient searching over vectorized data. It is configured automatically through the provided `docker-compose.yml` setup.

Run the docker compose file to start `redis` and `qdrant` services.

```bash
docker-compose up
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

### 6. Running the Application

Ensure you have uploaded documents into the `data_path` folder specified in your configuration file `config.yaml`. Make sure the paths exist(if running locally)

A sample test pdf is added in `./data/test/` for testing. Feel free to add other pdf, text, docx files for testing.

To run the streamlit application, navigate to the project directory and use the following command:

```bash
streamlit run src/streamlit-app.py
```

For querying without the Streamlit interface, you can use:

```bash
python -m src.pipeline --query "your search query here"
```
To test the application and check its output, you can use the Streamlit interface or directly interact with the command line interface as mentioned above.

## Evaluation

The Evaluation module is designed to assess the performance of the RAG Pipeline, specifically focusing on the quality of answers. 

It leverages a set of metrics to provide a comprehensive evaluation of the system's output compared to ground truth data.

### Interpreting the Results

The results will include metrics scores for each query in a json, providing insights into the quality of the answers. These metrics measure the component wise and end to end accuracy of the rag pipeline.

#### Metrics Explained:
- `faithfulness`: A generator based metric that measures how factually accurate is the generated answer. 
- `answer_relevancy`: A generator based metric that measures how relevant is the generated answer to the question.
- `contextual_precision`: A retrievar based metric that measures the signal to noise ratio of retrieved context. Requires ground truth.
- `contextual_recall`:  A retrievar based metric that measures whether it can retrieve all the relevant information required to answer the question. Requires ground truth.
- `contextual_relevancy`: A retrievar based metric that measures the relevancy of the retrieved context, calculated based on both the question and contexts.
- `coherence`: Checks alignment of answer with the question. It is custom LLM metric evaluated using model.

### Prerequisites for Evaluation

Ensure the system is set up as per the setup instructions above, with all dependencies installed and both Qdrant and Redis services running.

### Preparing the Dataset

1. Prepare a CSV file containing the questions and their corresponding ground truth answers. The CSV file should have at least two columns: `question` and `ground_truth`. There is a sample data in `./data/eval` folder that can be used for testing.

2. Place your dataset in an accessible directory and note the path to this CSV file for the evaluation process.

### Evaluation Metrics Configuration

The evaluation process utilizes a metrics configuration file. The configuration specifies the thresholds and models used for each metric, as outlined below:

- **Metrics**:
  - `answer_relevancy`, `faithfulness`, `contextual_precision`, `contextual_recall`, `contextual_relevancy`, `coherence`: Each metric is configured with a `threshold` indicating the minimum acceptable score.
- **Model Types**:
  - `api`: Utilizes OpenAI's API for metric evaluation, suitable for production environments where high accuracy is essential.
  - `custom`: Uses locally hosted LLM models for evaluation, offering flexibility and reduced costs at the expense of potential stability issues. Note: Custom model evaluation is currently experimental and may exhibit bugs, which will be addressed in future releases.
- **Model Selection**:
  - The `model` field specifies the model used for evaluation. For API model types, this typically refers to an OpenAI model identifier, such as `gpt-4-0125-preview` which is most suitable for the evaluation.
- **Thresholds**:
  - The `threshold` value for each metric defines the cut-off score for considering a response satisfactory. Scores above this threshold indicate acceptable performance on the metric.

#### Environment Setup for Evaluation

To perform evaluations using the `api` model type, you must set the `OPENAI_API_KEY` environment variable with your API key from OpenAI account [settings](https://platform.openai.com/api-keys). This key enables the application to authenticate with OpenAI's API for generating evaluation scores. Set the environment variable as follows before running evaluations:

```bash
export OPENAI_API_KEY='your_openai_api_key_here'
```
Ensure this variable is set in your environment to avoid authentication issues during the evaluation process.

### Running the Evaluation

The evaluation process involves executing the main script with appropriate arguments to specify the configuration file, data path, path to the QA CSV file, and an option to save the results.

1. **Navigate to the Project Directory**: Ensure you are in the root directory of the Enterprise Search project.

2. **Execute the Evaluation Script**: Use the following command to run the evaluation, replacing the placeholder paths with your actual file paths.

```bash
python src/eval.py --config_path config.yml --data_path ./data/eval/document/ --qa_csv_path ./data/eval/wiki-00001-qa.csv --save
```

- `--config_path`: Specifies the path to the YAML configuration file for the RAG Pipeline.
- `--data_path`: Indicates the directory where your documents for indexing are stored.
- `--qa_csv_path`: The path to the QA CSV file containing your evaluation dataset.
- `--save`: A flag that, when used, instructs the script to save the evaluation results to a file.

The script will process each question in the CSV file, perform a query against the indexed documents, and evaluate the responses using the specified metrics.

You can replace the dataset with your documents and relevant Q/A pairs.

Results will be logged and, if the `--save` flag is used, saved to a JSON file in the `./results` directory with a timestamped filename.

## Kubernetes/Helm Deployment to the DPC cluster

- The [README](k8s/README.md) file outlines the instructions on how to deploy Enterprise Search on a cluster using kubernetes and helm.

## Troubleshooting

- **Qdrant/Redis Connection Issues**: Ensure that Qdrant and Redis are running and accessible at the URLs and ports specified in `config.yml`.
- **Dependency Errors**: Make sure all Python dependencies are installed correctly as per `requirements.txt`.
- **Configuration Errors**: Verify that all paths and configurations in `config.yml` and `eval_metrics_config.yml` are correct and point to the right resources.

## Release Notes

Version 1.0.3 - 08/05/2024
- Updated pipeline and eval code to async mode
- Updated config and code structure to simplify config loading across app
- Updated logger and removed unwanted declarations throughout the code
- Fixed bugs for local testing (now docker compose works for local testing)
- Updated model to llama3 models in config.yaml
- Fixed runtime issues during API call.