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
streamlit run src/streamlit-app.py
```

For querying without the Streamlit interface, you can use:

```bash
python src/pipeline.py --query "your search query here"
```
To test the application and check its output, you can use the Streamlit interface or directly interact with the command line interface as mentioned above.

## Evaluation

The Evaluation module is designed to assess the performance of the RAG Pipeline, specifically focusing on the quality of answers. It leverages a set of metrics including faithfulness, answer relevancy, contextual relevancy, and coherence to provide a comprehensive evaluation of the system's output compared to ground truth data.

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

Version 1.0.2 - 08/04/2024
- Added deployment support to any k8s cluster using terraform.
- Fixed the ollama localhost issue in the llamaindex framework.
- Added support to pull and test multiple ollama models configurable during deployment.
- Bug Fixes and Improvements