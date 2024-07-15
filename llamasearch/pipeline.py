
from typing import Any, List, Tuple, Dict, Optional
from tabulate import tabulate
import asyncio
import os

from llamasearch.logger import logger
from llamasearch.latency import track_latency, LatencyTracker
from llamasearch.utils import load_yaml_file
from llamasearch.settings import config
from llamasearch.qdrant_hybrid_search import QdrantHybridSearch

from llama_index.postprocessor.flag_embedding_reranker import (
    FlagEmbeddingReranker,
)
from llama_index.storage.docstore.redis import RedisDocumentStore
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.embeddings import resolve_embed_model
from llama_index.core import PromptTemplate
from llama_index.llms.ollama import Ollama
from llama_index.core import SimpleDirectoryReader, Settings
from llama_index.core.ingestion import (
    DocstoreStrategy,
    IngestionPipeline,
    IngestionCache,
)
from llama_index.storage.kvstore.redis import RedisKVStore as RedisCache
from llama_index.core.response.pprint_utils import pprint_response

#import nest_asyncio
#nest_asyncio.apply()

class Pipeline:
    """
    Manages document processing and querying pipeline. Main operations:
    - Document loading and parsing
    - Embedding and indexing
    - Query processing and reranking
    - Context extraction and formatting
    """
    def __init__(self, config):
        self.config = config
        self.setup_llm()
        #self.setup_embed_model()
        self.reranker = None
        self.index = None
        self.qa_template = None
        self.prompt_template = ""
        self.qdrant_search = QdrantHybridSearch(config)
        self.is_setup_complete = False
        self.documents = None

    async def setup(self):
        if self.is_setup_complete:
            logger.info("Setup already completed. Skipping.")
            return

        setup_steps: List[tuple[str, callable]] = [
            ("Qdrant index", self.qdrant_search.setup_index_async),
            ("Docstore", self.setup_docstore),
            ("Parser", self.setup_parser),
            ("Reranker", self.setup_reranker),
            ("Documents", self.load_documents_async),
            ("Index creation", self.qdrant_search.create_index_async),
            ("Ingestion pipeline", self.setup_ingestion_pipeline),
            ("Query engine", self.setup_query_engine)
        ]

        for step_name, step_func in setup_steps:
            try:
                logger.info(f"Setting up {step_name}...")
                if step_name == "Documents":
                    self.documents = await step_func()
                elif step_name == "Ingestion pipeline":
                    await step_func()
                    nodes = await self.ingest_documents(self.documents)
                    await self.qdrant_search.add_nodes_to_index_async(nodes)
                else:
                    await step_func()
                logger.info(f"{step_name} setup completed.")
            except Exception as e:
                logger.error(f"Error during {step_name} setup: {str(e)}")
                raise
        self.is_setup_complete = True
        logger.info("All setup steps completed successfully.")

    async def setup_reranker(self, top_n=3):
        self.reranker = FlagEmbeddingReranker(
            top_n=top_n,
            model=config.reranker.model,
        )

    def setup_llm(self):
        """Initializes the Large Language Model (LLM) based on the configuration."""
        llm_config = load_yaml_file(config.llm.modelfile)
        model_settings = llm_config['model']
        model_name = model_settings.pop('name', None)
        if not model_name:
            raise ValueError("Model name is not specified in the model YAML {} configuration.")
        base_url = os.getenv('OLLAMA_SERVER_URL', 'http://localhost:11434')
        logger.info(f"Running model {model_name} on {base_url}")
        Settings.llm = Ollama(
            base_url=base_url,
            model=model_name,
            **model_settings
        )
        self.prompt_template = llm_config['prompts'][0]['text']

    def setup_embed_model(self):
        """Initializes the embedding model based on the configuration."""
        logger.info("Using embedding model : {}".format(config.embedding.model))
        Settings.embed_model = resolve_embed_model(config.embedding.model)

    async def setup_docstore(self):
        """
        Creates a docstore and adds the nodes to it.
        """
        self.docstore = RedisDocumentStore.from_host_and_port(
            host=self.config.redis_config.host, port=self.config.redis_config.port, namespace="llamasearch"
        )

    async def setup_parser(self):
        self.parser = SentenceSplitter()

    async def setup_ingestion_pipeline(self):
        self.ingestion = IngestionPipeline(
            transformations=[self.parser],
            docstore=self.docstore,
            vector_store=self.qdrant_search.vector_store,
            cache=IngestionCache(
                cache=RedisCache.from_host_and_port(
                        host=self.config.redis_config.host, 
                        port=self.config.redis_config.port
                    ),
                    collection="redis_cache",
                ),
            docstore_strategy=DocstoreStrategy.UPSERTS,
        )

    async def ingest_documents(self, documents):
        return await self.ingestion.arun(documents=documents)

    async def setup_query_engine(self):
        self.query_engine = self.qdrant_search.index.as_query_engine(
            node_postprocessors=[self.reranker]
        )

    @track_latency
    async def perform_query_async(self, query: str):
        if not self.is_setup_complete:
            raise RuntimeError("Pipeline setup is not complete. Call setup() first.")
        self.update_prompt()
        if hasattr(self, 'qa_template') and self.qa_template is not None:
            self.query_engine.update_prompts(
                {"response_synthesizer:text_qa_template": self.qa_template}
            )
        response = await self.query_engine.aquery(query)
        return response

    @track_latency
    async def load_documents_async(self, use_llamaparse=False):
        # if use_llamaparse:
        #     doc_list  = [os.path.join(self.config["documents_dir"], f) for f in os.listdir(self.config["documents_dir"]) if os.path.isfile(os.path.join(self.config["documents_dir"], f))]
        #     logger.info(doc_list)
        #     from llama_parse import LlamaParse
        #     documents = LlamaParse(result_type="markdown").load_data(doc_list)
        #     return documents
        documents = SimpleDirectoryReader(self.config.application.data_path).load_data()
        return documents

    def update_prompt(self):
        query_context_str = """
            Query:
            {query_str}

            Context:
            {context_str}

            Response:
        """
        template = (
            self.prompt_template+"\n"+query_context_str
        )
        self.qa_template = PromptTemplate(template)

    @staticmethod
    def get_context_from_response(response_object):
        """
        Extracts and logs document metadata from a response object, avoiding duplicate entries for the same document.

        Args:
            response_object: An object containing metadata about documents processed in a pipeline.
            Expected to have 'metadata' and 'source_nodes' attributes if present.
        Returns:
            tuple: A tuple containing:
                - A dictionary of (file path, details).
                - List of contents extracted from the 'source_nodes' that contribute to the response

        Iterating over the document's information. It compiles a dictionary of unique file paths with their respective details and logs a formatted
        summary of these details and maps it to the response.
        """
        document_info = {}
        retrieval_context = None
        if response_object:
            try:
                if hasattr(response_object, 'source_nodes'):
                    retrieval_context = [node.get_content() for node in response_object.source_nodes]
                if hasattr(response_object, 'metadata'):
                    for doc_id, info in response_object.metadata.items():
                        print("\n\n")
                        print(info)
                        print("\n\n")
                        file_path = info.get('file_path')
                        file_name = info.get('file_name')
                        # Check if this file_path or combination of file_name and doc_id already exists
                        if (file_path not in document_info and 
                            not any(d['file_name'] == file_name and d['doc_id'] == doc_id 
                                    for d in document_info.values())):
                            
                            document_info[file_path] = {
                                'file_name': file_name,
                                'last_modified_date': info.get('last_modified_date'),
                                'doc_id': doc_id
                            }
            except Exception as e:
                logger.error("An error occurred while processing the response object: {}".format(e))
        return document_info, retrieval_context

    def pretty_print_context(self, response):
        document_info, retrieval_context = self.get_context_from_response(response)
        print("\n--- Document Information ---")
        if document_info:
            headers = ["File Name", "Last Modified", "Doc ID"]
            table_data = [[info['file_name'], info['last_modified_date'], info['doc_id']] 
                          for info in document_info.values()]
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
        else:
            print("No document information available.")
        print("\n--- Retrieval Context ---")
        if retrieval_context:
            for i, context in enumerate(retrieval_context, 1):
                print(f"\nContext {i}:")
                print(context[:500] + "..." if len(context) > 500 else context)
        else:
            print("No retrieval context available.")

    def cleanup(self):
        self.qdrant_search.cleanup()

class PipelineFactory:
    def __init__(self):
        self.pipelines: Dict[str, Pipeline] = {}
        self.config = config

    async def create_pipeline_async(self, user_id: str) -> Pipeline:
        if user_id in self.pipelines:
            logger.info(f"Returning existing pipeline for user {user_id}")
            return self.pipelines[user_id]

        logger.info(f"Creating new pipeline for user {user_id}")
        pipeline = Pipeline(self.config.copy())

        try:
            await pipeline.setup()
            self.pipelines[user_id] = pipeline
            logger.info(f"Pipeline setup completed successfully for user {user_id}")
            return pipeline
        except Exception as e:
            logger.error(f"Error setting up pipeline for user {user_id}: {str(e)}")
            await self.cleanup_pipeline(user_id, pipeline)
            raise

    async def get_or_create_pipeline_async(self, user_id: str) -> Pipeline:
        pipeline = self.get_pipeline(user_id)
        if not pipeline:
            pipeline = await self.create_pipeline_async(user_id)
        return pipeline

    def get_pipeline(self, user_id: str) -> Pipeline:
        return self.pipelines.get(user_id)

    async def cleanup_pipeline(self, user_id: str, pipeline: Pipeline = None):
        if pipeline is None:
            pipeline = self.pipelines.pop(user_id, None)
        if pipeline:
            try:
                await pipeline.cleanup()
                logger.info(f"Pipeline cleaned up for user {user_id}")
            except Exception as e:
                logger.error(f"Error during pipeline cleanup for user {user_id}: {str(e)}")

    async def cleanup_all(self):
        for user_id in list(self.pipelines.keys()):
            await self.cleanup_pipeline(user_id)
        logger.info("All pipelines cleaned up")


async def main_async():
    try:
        factory = PipelineFactory()
        user_id = "123456"
        pipeline = await factory.get_or_create_pipeline_async(user_id)
        while True:
            query = input("Enter your query (or 'quit' to exit): ").strip()
            if query.lower() == "quit":
                break
            try:
                response = await pipeline.perform_query_async(query)
                pprint_response(response, show_source=True)
                print("\n\n")
                logger.info(f"Response: {response}")
                pipeline.pretty_print_context(response)
                LatencyTracker().print_summary()
            except Exception as e:
                logger.info(f"An error occurred during query: {e}")
    except Exception as err:
        logger.error(f"An error occurred: {err}")
    finally:
        LatencyTracker().report_stats()
        await factory.cleanup_all()

if __name__ == "__main__":
    asyncio.run(main_async())
