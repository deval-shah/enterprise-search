## Evaluation

The Evaluation module is designed to assess the performance of the RAG Pipeline, specifically focusing on the quality of answers. 

It leverages a set of metrics to provide a comprehensive evaluation of the system's output compared to ground truth data.

### Interpreting the Results

The results will include metrics scores for each query in a json, providing insights into the quality of the answers. These metrics measure the component wise and end to end accuracy of the rag pipeline.

#### Metrics Explained:
- `faithfulness`: A generator based metric that measures how factually accurate is the generated answer. 
- `answer_relevancy`: A generator based metric that measures how relevant is the generated answer to the question.
- `contextual_precision`: A retriever based metric that measures the signal to noise ratio of retrieved context. Requires ground truth.
- `contextual_recall`:  A retriever based metric that measures whether it can retrieve all the relevant information required to answer the question. Requires ground truth.
- `contextual_relevancy`: A retriever based metric that measures the relevancy of the retrieved context, calculated based on both the question and contexts.
- `coherence`: Checks alignment of answer with the question. It is custom LLM metric evaluated using model.

### Prerequisites

Ensure the system is set up as per the setup instructions above, with all dependencies installed and both Qdrant and Redis services running.

### Preparing the Dataset

1. Prepare a json file containing the questions and their corresponding ground truth answers. The json file should have at least four keys: `queries` and `response`{ground truth} `relevant_docs` {query_id, nodeid k,v pairs} and `corpus` {node of origin for the query}. There is a sample data in `./data/eval` folder that can be used for testing.

2. Place your dataset in an accessible directory and note the path to this CSV file for the evaluation process.


### Generating Synthetic Dataset
To evaluate the pipeline, a synthetic dataset based on the nodes(chunks) in the pipeline can be generated. This dataset will consist of question-answer pairs derived from the nodes, allowing for both end-to-end and component-wise evaluation of the pipeline.


```bash
python -m  llamasearch.eval_data_generation --data_path ./data/eval/document/ --qa_json_path ./data/eval --save --node_limit 1

- `--data_path`: Indicates the directory where your documents for indexing are stored.
- `--qa_json_path`: The path to the QA json file containing your evaluation dataset.
- `--save`: A flag that, when used, instructs the script to save the evaluation results to a file.
```

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


### Running the Evaluation Pipeline

The evaluation pipeline has been setup to run on DVC to track the pipeline results. Use the following command to execute the pipeline.
```bash 
dvc repro
```
This should execute the pipeline in three stages, as follows:

### DVC Stages

#### 1. data_pull
A dataset has already been generated and stored in the google cloud bucket.

#### 2. evaluate 
The evaluation process involves executing the main script with appropriate arguments to specify the configuration file, data path, path to the QA CSV file, and an option to save the results in json `.data/eval_results/evaluation_result_metrics.json`. 
The pipeline has been setup to evaluate one Question & Answer Pair, to increase the limit toggle the `--limit` option in the `dvc.yaml`

#### 3. analyse  
This stage analyzes model evaluation results stored in a JSON file and calculate performance metrics. It computes the mean, median, and standard deviation for the metrics. It  then saves the results to a CSV file  `data/eval_results/eval_metrics.csv` along with additional metadata (timestamp, model used, and optional side note) and a bar plot comparing the mean of evaluation metrics over different runs is also generated and saved as image `.data/eval_results/evaluation_result_metrics.json`.



 ### Results:
 The current run shows the mean score of each metrics on sentence splitter. More of it can be analzsed by referring `./data/eval_results/eval_metrics.csv`.


 ![alt text](../assets/results_evaluation.png)

 | Metric                    |     Mean |   Median |   Standard Deviation | Run Timestamp       | Model Used   | Side Note          |
|:--------------------------|---------:|---------:|---------------------:|:--------------------|:-------------|:-------------------|
| ContextualPrecisionMetric  | 0.790433 | 1        |             0.322457 | 2024-09-11 17:27:02 | llama3       | Initial evaluation  |
| ContextualRecallMetric     | 0.907876 | 1        |             0.253418 | 2024-09-11 17:27:02 | llama3       | Initial evaluation  |
| FaithfulnessMetric         | 0.918978 | 1        |             0.238641 | 2024-09-11 17:27:02 | llama3       | Initial evaluation  |
| AnswerRelevancyMetric      | 0.930791 | 1        |             0.203652 | 2024-09-11 17:27:02 | llama3       | Initial evaluation  |
| ContextualRelevancyMetric  | 0.770308 | 1        |             0.373611 | 2024-09-11 17:27:02 | llama3       | Initial evaluation  |
| Coherence                  | 0.768505 | 0.874086 |             0.258601 | 2024-09-11 17:27:02 | llama3       | Initial evaluation  |
