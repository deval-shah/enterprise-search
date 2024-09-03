

import timeit
import os
import csv
from tqdm import tqdm
import re
import uuid
import warnings
import json
import argparse

from llamasearch.embeddings import generate_qa_embedding_pairs
from llamasearch.settings import config

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openai import OpenAI

from ollama import Client
from llama_index.llms.ollama import Ollama
from llama_index.core import Document
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llamasearch.logger import logger
# from Ragflow import RagflowNodeParser

class DatasetGenerator:
    """
        This class encapculates the synthetic dataset generation pipeline
        Attributes:
        data_path (str): Directory path of the knowledge base.
        result_file_path (str): Directory path where evaluation results are saved.
    """
    def __init__(self, data_path: str, result_file_path: str):
        """
        Initializes the Evaluation instance with the data and result paths.

        Args:
            data_path: Path to the data directory.
            result_file_path: Path to output results file.
        """
        self.data_path=data_path
        self.config=config
        self.result_file_path=result_file_path
        self.parser=SentenceSplitter()
        self.num_questions_per_chunk=2
        self.llm=self.setup_model()
        self.QUESTION_PROMPT_TEMPLATE = """\
                Given a text, generate {n_questions} questions that could be asked about that topic.
                The topic is: {sub_topic}
                
                The list must be without numbers. The questions should be separated by a newline character. There must be no other text than the list.
        """
        self.TOPIC_GENERATION_PROMPT_TEMPLATE = """\
                Given a text, generate a list of {n_subtopics} subtopics that are related to the topic.

                The text is: {topic}

                The subtopics should be contextually relevant to the text. The list must be without numbers, and without any description of the subtopics. The subtopics should be separated by a comma. There must be no other text than the list.
                """
        self.RESPONSE_PROMPT_TEMPLATE= """\
            Given a question and context, generate a responses that could be the ground truth. The response should be precise.

            The question is: {question}

            The context is :  {context}

            Your response should be precise and concise.
                """
    
    def setup_model(self):
        logger.info("Setting up model")
        if self.config.dataset_generator.use_openai:
            self.llm=OpenAI(temperature=0, model=self.config.dataset_generator.model_name)
            return self.llm
        self.llm=Ollama(model=self.config.dataset_generator.model_name, request_timeout=120.0)
        return self.llm

    def save_results(self,path:str) -> None:
        """Saves the accumulated results to the specified results file."""
        with open(self.result_file_path, 'w', encoding='utf-8') as f:
            json.dump(path, f, ensure_ascii=False, indent=4)
        logger.info(f"Results saved to {self.result_file_path}")
    
    
     
    def generate_dataset(self,save_results_flag:bool) -> None:
        documents = SimpleDirectoryReader(self.data_path).load_data()
        nodes = self.parser.get_nodes_from_documents(documents)
        for idx, node in enumerate(nodes):
            node.id_ = f"node_{idx}"
        self.results = generate_qa_embedding_pairs(
        nodes, llm=self.llm, num_questions_per_chunk=self.num_questions_per_chunk)
        path=f"{self.result_file_path}/qna_dataset_{timeit.timeit()}.json"
        if save_results_flag:
                self.save_results(path)
        
    
    

    def generate_question_from_subtopics(self,n_questions:int) -> None:
        documents = SimpleDirectoryReader("data").load_data()
        nodes = self.parser.get_nodes_from_documents(documents)
        for idx, node in enumerate(nodes):
            node.id_ = f"node_{idx}"
        
        node_dict = {
        node.node_id: node.get_content()
        for node in nodes
    }
        
        queries = {}
        relevant_docs = {}
        responses={}
        for node_id, text in tqdm(node_dict.items()):
            subtopic=self.generate_subtopics(text)
            subtopics=str(subtopic).split(',')
            prompt = self.QUESTION_PROMPT_TEMPLATE.format(sub_topic=subtopics, n_questions=n_questions)
            response=self.llm.complete(prompt=prompt)
            result = str(response).strip().split("\n")
            questions = [
            re.sub(r"^\d+[\).\s]", "", question).strip() for question in result
            ]
            questions = [question for question in questions if len(question) > 0][
            :self.num_questions_per_chunk
        ]
            for question in questions:
                question_id = str(uuid.uuid4())
                queries[question_id] = question
                responses[question_id]=self.generate_responses(question,node_dict[node_id])
                relevant_docs[question_id] = [node_id]

                # print(responses[question_id])
        dataset={'queries':queries,'responses':responses,'corpus':node_dict,'relevant_docs':relevant_docs}
        with open(f"{self.result_file_path}/dataset.json", 'w') as fp:
            json.dump(dataset, fp,indent=4)
        # dataset.save_json(f"{self.result_file_path}/dataset.json")

    def generate_responses(self, question:str,context:str) ->str:
        prompt = self.RESPONSE_PROMPT_TEMPLATE.format(question=question,context=context)
        response = self.llm.complete(prompt=prompt)
        return str(response)
    

    def generate_subtopics(self,text:str,n_subtopics:int=1) -> str:
        prompt = self.TOPIC_GENERATION_PROMPT_TEMPLATE.format(topic=text, n_subtopics=n_subtopics)
        response = self.llm.complete(prompt=prompt)
        return response
       
    

if __name__=="__main__":
    parser = argparse.ArgumentParser(description="Evaluate LLaMA Index Questions and Answers.")
    parser.add_argument("--data_path", required=True, help="Path to the data directory.")
    parser.add_argument("--qa_json_path", required=True, help="Path to the QA JSON file.")
    parser.add_argument("--save", action="store_true", help="Flag to save the evaluation results.")
    args = parser.parse_args()
    generator=DatasetGenerator(data_path=args.data_path,result_file_path=args.qa_json_path)
    generator.generate_dataset(save_results_flag=True)
    

