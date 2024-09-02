

import timeit
import os
import csv
from tqdm import tqdm
import re
import uuid
import warnings
import json

from llamasearch.embeddings import generate_qa_embedding_pairs


from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openai import OpenAI

from llama_index.core.evaluation import (
    generate_question_context_pairs,
    EmbeddingQAFinetuneDataset,
)

from ollama import Client
from llama_index.llms.ollama import Ollama
from llama_index.core import Document
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.extractors import TitleExtractor
from llama_index.core.ingestion import IngestionPipeline, IngestionCache

from Ragflow import RagflowNodeParser

class RetriverEval:
    def __init__(self,llm_question_generator=None,llm_subtopic_generator=None):
        self.llm_question_generator=llm_question_generator
        self.llm_subtopic_generator=llm_subtopic_generator
        self.input_path="./data"
        self.output_path="./qna_pair_dataset"
        self.config_recorder="config_record.csv"
        self.parser=SentenceSplitter(chunk_size=512)
        self.congfig_file_path="./all_config_log.csv"
        self.num_questions_per_chunk=4
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
    def evaluate(self):
        start=timeit.timeit()
        path=self.generate_dataset()
        end=timeit.timeit()
        self.log_config(type(llm),str(end-start),path)


     
    def generate_dataset(self):
        documents = SimpleDirectoryReader("data").load_data()
        nodes = self.parser.get_nodes_from_documents(documents)
        print(len(nodes))
        for idx, node in enumerate(nodes):
            node.id_ = f"node_{idx}"
        qa_dataset = generate_qa_embedding_pairs(
        nodes, llm=self.llm_question_generator, num_questions_per_chunk=self.num_questions_per_chunk)
        path=f"{self.output_path}/qna_dataset_{timeit.timeit()}.json"
       
        with open(f"{self.output_path}/dataset.json", 'w') as fp:
            json.dump(qa_dataset, fp,indent=4)
        return path
    
    

    def generate_question_from_subtopics(self,n_questions):
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
            response=self.llm_question_generator.complete(prompt=prompt)
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
        with open(f"{self.output_path}/dataset.json", 'w') as fp:
            json.dump(dataset, fp,indent=4)
        # dataset.save_json(f"{self.output_path}/dataset.json")

    def generate_responses(self, question,context):
        prompt = self.RESPONSE_PROMPT_TEMPLATE.format(question=question,context=context)
        response = self.llm_question_generator.complete(prompt=prompt)
        return str(response)
    

    def generate_subtopics(self,text,n_subtopics=1):
        prompt = self.TOPIC_GENERATION_PROMPT_TEMPLATE.format(topic=text, n_subtopics=n_subtopics)
        response = self.llm_subtopic_generator.complete(prompt=prompt)
        return response

    def log_config(self, llm, time, path):
        data = {
            'model': llm,
            'time': time,
            'no.of qna pair': self.n_qa_pair,
            'path': path
        }
        file_exists = os.path.isfile(self.congfig_file_path)

       
        with open(self.congfig_file_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)

         
            if not file_exists:
                header = data.keys() 
                writer.writerow(header)

           
            writer.writerow(data.values())
    
    

if __name__=="__main__":
    llm=Ollama(model="llama3:latest", request_timeout=120.0)
    # llm = OpenAI(temperature=0, model="gpt-4o-mini")
    eval=RetriverEval(llm_question_generator=llm,llm_subtopic_generator=llm)
    eval.generate_dataset()
    

