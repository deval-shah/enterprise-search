from typing import List, Dict, Any
from deepeval.test_case import LLMTestCase
import csv
import json
import os
import signal
from datetime import datetime
import argparse
import asyncio
import warnings

from llamasearch.settings import config
from llamasearch.pipeline import Pipeline
from llamasearch.metrics import MetricsEvaluator
from llamasearch.logger import logger
import numpy as np


metrics_to_evaluate = ['contextual_precision','contextual_recall','faithfulness', 'answer_relevancy', 'contextual_relevancy', 'coherence']

class Eval:
    """
    This class encapsulates the evaluation of the RAG pipeline

    Attributes:
        data_path (str): Directory path of the knowledge base.
        results_file__path (str): Directory path where evaluation results are saved.
    """
    def __init__(self, data_path: str, results_file_path: str):
        """
        Initializes the Evaluation instance with the data and result paths.

        Args:
            data_path: Path to the data directory.
            results_file_path: Path to output results file.
        """
        self.data_path = data_path
        self.mobj = MetricsEvaluator()
        self.rag_pipeline = Pipeline(tenant_id = "tenant1", config=config)
        self.results_file_path = results_file_path
        self.results = self.load_existing_results()
        if self.data_path:
            self.rag_pipeline.if_eval_mode=True
            self.rag_pipeline.data_path = self.data_path
        self.metric_scores = {self.mobj.get_metric_name(self.mobj.metrics[metric_name]): [] for metric_name in metrics_to_evaluate}
        # Setup signal handlers to save results on interruption
        self.config=config
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    async def init_rag_pipeline(self):
        """
        Initializes the RAG pipeline

        Raises:
            Exception: If any step in initializing the pipeline fails.
        """
        try:
            self.rag_pipeline.is_eval_mode=True
            await self.rag_pipeline.setup()
            # nodes = await self.rag_pipeline.run_pipeline()
            # await self.rag_pipeline.index_documents(nodes)
            logger.info("RAG pipeline initialization successful.")
        except Exception as e:
            logger.error(f"Failed to initialize RAG pipeline: {e}")
            raise
    
    async def evaluate(self, idx: int, input_query: str, ground_truth: str=None) -> None:
        response_object = await self.rag_pipeline.perform_query_async(input_query)
        if response_object is None:
            logger.error("Failed to retrieve response from query application.")
            return
        actual_output = response_object.response
        retrieval_context = [node.get_content() for node in response_object.source_nodes]
        logger.info("Evaluating ....")
        metrics_results = []
        if actual_output and retrieval_context:
            for metric_name in metrics_to_evaluate:
                metric_result = self._evaluate_metric(input_query, actual_output, retrieval_context, ground_truth, self.mobj.metrics[metric_name])
                metrics_results.append(metric_result)

        # Append the result for this evaluation to the results list
        self.results.append({
            "id": idx,
            "question": input_query,
            "ground_truth": ground_truth,
            "es_answer": actual_output,
            "metrics": metrics_results,
            "context": retrieval_context
        })

    def _evaluate_metric(self, input: str, output: str, retrieval_context: List[str], ground_truth: str, metric) -> None:
        """
        Evaluates the given metric for the test case.

        Args:
            input: The input query string.
            output: The actual output response from the query application.
            retrieval_context: The retrieval context fetched from vector db as per the query.
            metric: The metric evaluator object to be used for evaluation.
        """
        test_case = LLMTestCase(input=input, actual_output=output, retrieval_context=retrieval_context)
        if ground_truth:
            test_case = LLMTestCase(input=input, expected_output=ground_truth, actual_output=output, retrieval_context=retrieval_context)
        try:
            metric.measure(test_case)
            metric_name = self.mobj.get_metric_name(metric)
            logger.info(f"Metric: {metric_name}")
            logger.info(f"Actual Output: {output}")
            score = getattr(metric, 'score', -1)
            if score is not None:
                logger.info(f"Metric Score: {score}")
            reason = getattr(metric, 'reason', '-')
            if reason is not None:
                logger.info(f"Metric Reason: {reason}")
            self.metric_scores[metric_name].append(score)
            return {"name": self.mobj.get_metric_name(metric), "score": score, "reason": reason}
        except Exception as e:
            logger.error(f"Error evaluating metric {self.mobj.get_metric_name(metric)}: {e}")
    
    def load_csv_to_dict(self, csv_path: str) -> List[Dict[str, Any]]:
        """
        Load CSV content from a given path into a list of dictionaries.

        Args:
            csv_path (str): The file path to the CSV file.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries (Question, Answer) pairs representing the rows in the CSV file.
        """
        try:
            with open(csv_path, mode='r', encoding='utf-8') as csv_file:
                reader = csv.DictReader(csv_file)
                return [row for row in reader]
        except FileNotFoundError:
            raise FileNotFoundError(f"The file at {csv_path} was not found.")
        except Exception as e:
            raise Exception(f"An error occurred while processing the file at {csv_path}: {e}")
   
    def load_json(self,json_path:str):
            """
            Load JSON content from a given path
            
            """
            with open(json_path) as json_data:
                data = json.load(json_data)
            return data

    def load_existing_results(self) -> List[Dict[str, Any]]:
        """Loads existing results from the results file if it exists."""
        if os.path.isfile(self.results_file_path):
            with open(self.results_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    async def save_results(self) -> None:
        """Saves the accumulated results to the specified results file."""
        with open(self.results_file_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=4)
        logger.info(f"Results saved to {self.results_file_path}")

    def signal_handler(self, signum, frame):
        """Signal handler to save results upon receiving interruption signals."""
        logger.info("Interrupt signal received. Saving results...")
        self.save_results()
        self.display_stats()
        exit(1)

    async def display_stats(self):
        """
        Display statistics for each metric evaluated.
        Prints the mean, median, and standard deviation for the metric scores using logger.info in a single line.
        """
        stats_summary = []
        for metric_name, scores in self.metric_scores.items():
            if scores:  # Ensure there are scores to calculate statistics
                mean_score = np.mean(scores)
                median_score = np.median(scores)
                std_score = np.std(scores)
                stats_summary.append(f"{metric_name}: Mean={mean_score:.2f}, Median={median_score:.2f}, Std Dev={std_score:.2f}")

        # Join all metric summaries into a single line and log it
        logger.info(" | ".join(stats_summary))

async def main(data_path: str, qa_json_path: str, save_results_flag: bool):
    """
    Main function to run the evaluation process.
    
    Args:
        data_path: Path to the data directory.
        qa_json_path: Path to the QA CSV file.
        save_results_flag: Flag indicating whether to save results to a file.
    """
    results_dir = "./results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file_path = os.path.join(results_dir, f"eval_{timestamp}.json")
    try:
        logger.info("Initialising the pipeline for evaluation....")
        eval_instance = Eval(data_path, results_file_path)
        await eval_instance.init_rag_pipeline()
        print("-"*120)
        json_content = eval_instance.load_json(qa_json_path)
        for idx, query in json_content['queries'].items():
            input_query = query
            ground_truth = json_content['responses'][idx]
            logger.info(f"Evaluating: ID {idx} | Question: {input_query} | Ground Truth: {ground_truth}")
            await eval_instance.evaluate(idx, input_query, ground_truth)
            if save_results_flag:
                await eval_instance.save_results()
            await eval_instance.display_stats()
            print("-"*120)
       
    except Exception as e:
        logger.error(f"Error during evaluation: {e}")
        exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate LLaMA Index Questions and Answers.")
    parser.add_argument("--data_path", required=True, help="Path to the data directory.")
    parser.add_argument("--qa_json_path", required=True, help="Path to the QA CSV file.")
    parser.add_argument("--save", action="store_true", help="Flag to save the evaluation results.")
    args = parser.parse_args()
    asyncio.run(main(args.data_path, args.qa_json_path, args.save))
