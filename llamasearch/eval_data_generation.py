"""A generate synthetic Question & Answer datasets from nodes/document chunks"""
import datetime
from tqdm import tqdm
import re
import uuid
import warnings
import json
import argparse

from typing import Dict, List, Tuple
from llamasearch.settings import config

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openai import OpenAI

from ollama import Client
from llama_index.llms.ollama import Ollama
from llama_index.core import Document
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.bridge.pydantic import BaseModel
from llama_index.core.llms.utils import LLM
from llama_index.core.schema import MetadataMode, TextNode
from llamasearch.logger import logger

# from Ragflow import RagflowNodeParser

class EmbeddingQAFinetuneDataset(BaseModel):
    """Embedding QA Finetuning Dataset.

    Args:
        queries (Dict[str, str]): Dict id -> query.
        corpus (Dict[str, str]): Dict id -> string.
        relevant_docs (Dict[str, List[str]]): Dict query id -> list of doc ids.

    """

    queries: Dict[str, str]  # dict id -> query
    corpus: Dict[str, str]  # dict id -> string
    relevant_docs: Dict[str, List[str]]  # query id -> list of doc ids
    mode: str = "text"

    @property
    def query_docid_pairs(self) -> List[Tuple[str, List[str]]]:
        """Get query, relevant doc ids."""
        return [
            (query, self.relevant_docs[query_id])
            for query_id, query in self.queries.items()
        ]

    def save_json(self, path: str) -> None:
        """Save json."""
        with open(path, "w") as f:
            json.dump(self.dict(), f, indent=4)

    @classmethod
    def from_json(cls, path: str) -> "EmbeddingQAFinetuneDataset":
        """Load json."""
        with open(path) as f:
            data = json.load(f)
        return cls(**data)


DEFAULT_QA_GENERATE_PROMPT_TMPL = """\
Context information is below.

---------------------
{context_str}
---------------------

Given the context information and not prior knowledge.
generate only {num_questions_per_chunk} questions.\
Please generate a clear and concise question. \
It requires understanding of the content provided in the document chunk. \
Ensure that the question is specific, relevant, and not too broad."
"""
RESPONSE_PROMPT_TEMPLATE= """\
            Given a question and context, generate a responses that could be the ground truth. The response should be precise.

            The question is: {question}

            The context is :  {context}

            Your response should be precise and concise.
                """

# generate queries as a convenience function
def generate_qa_embedding_pairs(
    nodes: List[TextNode],
    llm: LLM,
    qa_generate_prompt_tmpl: str = DEFAULT_QA_GENERATE_PROMPT_TMPL,
    num_questions_per_chunk: int = 2,
) -> EmbeddingQAFinetuneDataset:
    """Generate examples given a set of nodes."""
    node_dict = {
        node.node_id: node.get_content(metadata_mode=MetadataMode.NONE)
        for node in nodes
    }

    queries = {}
    responses={}
    relevant_docs = {}
    for node_id, text in tqdm(node_dict.items()):
        query = qa_generate_prompt_tmpl.format(
            context_str=text, num_questions_per_chunk=num_questions_per_chunk
        )
        response = llm.complete(query)

        result = str(response).strip().split("\n")
        questions = [
            re.sub(r"^\d+[\).\s]", "", question).strip() for question in result
        ]
        questions = [question for question in questions if len(question) > 0][
            :num_questions_per_chunk
        ]

        num_questions_generated = len(questions)
        if num_questions_generated < num_questions_per_chunk:
            warnings.warn(
                f"Fewer questions generated ({num_questions_generated}) "
                f"than requested ({num_questions_per_chunk})."
            )

        for question in questions:
            question_id = str(uuid.uuid4())
            queries[question_id] = question
            relevant_docs[question_id] = [node_id]
            responses[question_id]=generate_responses(llm,question,node_dict[node_id])
        dataset={'queries':queries,'responses':responses,'corpus':node_dict,'relevant_docs':relevant_docs}
    return dataset

def generate_responses( llm,question,context):
        prompt = RESPONSE_PROMPT_TEMPLATE.format(question=question,context=context)
        response = llm.complete(prompt=prompt)
        return str(response)
class DatasetGenerator:
    """
        This class encapculates the synthetic dataset generation pipeline
        Attributes:
        data_path (str): Directory path of the knowledge base.
        result_file_path (str): Directory path where evaluation results are saved.
    """
    def __init__(self, data_path: str, result_file_path: str, no_node_limit:int=None):
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
        self.num_questions_per_chunk=1
        self.llm=self.setup_model()
        self.no_node_limit=no_node_limit
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
            self.llm=OpenAI(temperature=0,timeout=600, model=self.config.dataset_generator.openai_model)
            return self.llm
        self.llm=Ollama(model=self.config.dataset_generator.model_name, request_timeout=120.0)
        return self.llm

    def save_results(self,path:str) -> None:
        """Saves the accumulated results to the specified results file."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.dataset, f, ensure_ascii=False, indent=4)
        logger.info(f"Results saved to {path}")
    
    
     
    def generate_dataset(self,save_results_flag:bool) -> None:
        documents = SimpleDirectoryReader(self.data_path).load_data()
        nodes = self.parser.get_nodes_from_documents(documents)
        if self.no_node_limit:
            nodes=nodes[:self.no_node_limit]
        for idx, node in enumerate(nodes):
            node.id_ = f"node_{idx}"
        self.dataset = generate_qa_embedding_pairs(
        nodes, llm=self.llm, num_questions_per_chunk=self.num_questions_per_chunk)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path=f"{self.result_file_path}/qna_dataset_{timestamp}.json"
        if save_results_flag:
                self.save_results(path)
        return self.dataset
        
    
    

    def generate_question_from_subtopics(self, save_results_flag:bool) -> None:
        documents = SimpleDirectoryReader("data").load_data()
        nodes = self.parser.get_nodes_from_documents(documents)
        if self.no_node_limit:
            nodes=nodes[:self.no_node_limit]
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
            prompt = self.QUESTION_PROMPT_TEMPLATE.format(sub_topic=subtopics, n_questions=self.num_questions_per_chunk)
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
        self.dataset={'queries':queries,'responses':responses,'corpus':node_dict,'relevant_docs':relevant_docs}
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path=f"{self.result_file_path}/qna_dataset_{timestamp}.json"
        if save_results_flag:
                self.save_results(path)

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
    parser.add_argument("--node_limit", type=int, required=False, default=None, help="Limit the number of self.nodes to process (must be a positive integer).")
    args = parser.parse_args()
    generator=DatasetGenerator(data_path=args.data_path,result_file_path=args.qa_json_path,no_node_limit=int(args.node_limit))
    generator.generate_dataset(save_results_flag=True)
    

