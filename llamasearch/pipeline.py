
from typing import Any, List, Tuple, Dict, Optional
from tabulate import tabulate
import asyncio
import os

from llamasearch.logger import logger
from llamasearch.latency import track_latency, LatencyTracker
from llamasearch.utils import load_yaml_file, ensure_dummy_csv
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

ALLOWED_EXTS = [".pdf", ".docx", ".csv"]
HARD_LIMIT_FILE_UPLOAD = 10

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
        self.setup_embed_model()
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
            ("Documents", lambda: self.load_documents_async(data_dir=self.config.application.data_path)),
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
                    logger.info(f"Ingesting {len(nodes)} nodes for {len(self.ingestion.docstore.docs)} chunks")
                    await self.qdrant_search.add_nodes_to_index_async(nodes)
                    logger.info("Ingestion pipeline setup completed.")
                else:
                    await step_func()
                logger.info(f"{step_name} setup completed.")
            except Exception as e:
                logger.error(f"Error during {step_name} setup: {str(e)}")
                raise
        self.is_setup_complete = True
        logger.info("All setup steps completed successfully.")

    async def setup_reranker(self):
        self.reranker = FlagEmbeddingReranker(
            top_n=self.config.reranker.top_n,
            model=self.config.reranker.model,
        )

    def setup_llm(self):
        """Initializes the Large Language Model (LLM) based on the configuration."""
        if self.config.llm.use_openai:
            logger.info("Using OpenAI for generation...")
            # TODO :: Pass model settings from config to init the openai llm model
            # TODO :: Override the openai client with external
            return
        llm_config = load_yaml_file(self.config.llm.modelfile)
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

    # TODO :: Embedding model should be shared across users, we should not init embed models for each user (for local model)
    def setup_embed_model(self):
        if self.config.embedding.use_openai:
            logger.info("Using OpenAI for embeddings...")
            "By default LlamaIndex uses openai:text-embedding-ada-002, which is the default embedding used by OpenAI"
            # TODO :: Pass embed model settings from config to init the openai embed model
            return
        """Initializes the embedding model based on the configuration."""
        logger.info("Using embedding model : {}".format(self.config.embedding.model))
        Settings.embed_model = resolve_embed_model(self.config.embedding.model)

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
        # TODO :: Configure qa template from modelfile
        qa_prompt_tmpl_str = (
            "Context information is below.\n"
            "---------------------\n"
            "{context_str}\n"
            "---------------------\n"
            "Given the context information and not prior knowledge, "
            "answer the query in concise form.\n"
            "Query: {query_str}\n"
            "Answer: "
        )
        qa_prompt_tmpl = PromptTemplate(qa_prompt_tmpl_str)

        top_k = self.config.vector_store_config.top_k
        enable_hybrid = self.config.vector_store_config.enable_hybrid
        query_engine_kwargs = {
            "node_postprocessors": [self.reranker],
            "similarity_top_k": top_k,
            "response_mode":"compact"
        }

        if enable_hybrid:
            logger.debug("Hybrid search is enabled...")
            query_engine_kwargs["vector_store_query_mode"] = "hybrid"
        self.query_engine = self.qdrant_search.index.as_query_engine(**query_engine_kwargs)
        self.query_engine.update_prompts(
            {"response_synthesizer:text_qa_template": qa_prompt_tmpl}
        )

    @track_latency
    async def perform_query_async(self, query: str):
        await self.setup_query_engine()
        if not self.is_setup_complete:
            raise RuntimeError("Pipeline setup is not complete. Call setup() first.")
        response = await self.query_engine.aquery(query)
        return response

    async def insert_documents(self, file_paths):
        documents = await self.load_documents_async(input_files=file_paths)
        for doc in documents:
            logger.debug(f"Processing Document ID: {doc.id_}")
        nodes = await self.ingest_documents(documents)
        logger.info(f"Insertion :: Ingesting {len(nodes)} nodes for {len(self.ingestion.docstore.docs)} chunks")
        await self.qdrant_search.add_nodes_to_index_async(nodes)
        return nodes

    # async def get_ref_info(self):
    #     try:
    #         all_ref_doc_info = self.qdrant_search.index.ref_doc_info
    #         pprint(dict(list(all_ref_doc_info.items())[:5]), width=100, compact=True)
    #     except Exception as e:
    #         logger.error(f"Error getting ref_doc_info: {e}")

    # Delete a document from index and docstore
    # TODO :: Issue with deleting from docstore not fixed yet
    async def delete_document_using_id(self, doc_id, delete_from_docstore=True):
        try:
            if self.qdrant_search.index is None:
                print(f"Error: The index is not initialized in qdrant_search.")
                return
            # Check if the document exists in the index
            # if doc_id not in qdrant_search.index.docstore.docs:
            #     print(f"Document with ID {doc_id} is not in the index. Nothing to delete.")
            #     return
            # Delete the document from the index
            self.qdrant_search.index.delete_ref_doc(doc_id, delete_from_docstore=delete_from_docstore)
            logger.info(f"Document with ID {doc_id} has been deleted from the index.")
            if delete_from_docstore:
                logger.info(f"Document with ID {doc_id} has also been deleted from the docstore.")
            else:
                logger.info(f"Document with ID {doc_id} remains in the docstore but will not be used for querying.")        
        except Exception as e:
            logger.error(f"Error deleting document with ID {doc_id}: {str(e)}")

    @track_latency
    async def load_documents_async(self, data_dir=None, input_files=None, use_llamaparse=False):
        # if use_llamaparse:
        #     doc_list  = [os.path.join(self.config["documents_dir"], f) for f in os.listdir(self.config["documents_dir"]) if os.path.isfile(os.path.join(self.config["documents_dir"], f))]
        #     logger.info(doc_list)
        #     from llama_parse import LlamaParse
        #     documents = LlamaParse(result_type="markdown").load_data(doc_list)
        #     return documents
        reader_kwargs = {
            "filename_as_id": True,
            "required_exts": ALLOWED_EXTS,
            "num_files_limit": HARD_LIMIT_FILE_UPLOAD
        }
        if data_dir:
            reader_kwargs["input_dir"] = data_dir
            reader_kwargs["recursive"] = False
        elif input_files:
            reader_kwargs["input_files"] = [input_files] if isinstance(input_files, str) else input_files
        else:
            raise ValueError("Please provide either data_path or input_files.")
        documents = SimpleDirectoryReader(**reader_kwargs).load_data()
        return documents

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
                        # print("\n\n")
                        # print(info)
                        # print("\n\n")
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

# TODO :: Background worker to assign pipeline init tasks (celery q?)
# TODO :: Pipeline pool implementation to keep the pipelines ready upon server start
class PipelineFactory:
    def __init__(self, is_api_server=False):
        self.pipelines: Dict[str, Pipeline] = {}
        self.config = config
        self.is_api_server = is_api_server

    async def initialize_common_resources(self):
        # TODO :: Initialize any shared resources here
        pass

    async def override_user_data_path(self, user_id: str) -> str:
        upload_dir = os.path.join(self.config.application.data_path, self.config.application.upload_subdir)
        user_dir = os.path.join(upload_dir, user_id)
        os.makedirs(user_dir, exist_ok=True)
        # Hack to ensure we have a file in upload to init the pipeline to init the vector index
        # without having wait during the first query call (will remove later)
        ensure_dummy_csv(user_dir)
        logger.info("User upload directory updated to: " + user_dir)
        # Overriding the local config path to user specific directory for file uploads
        self.config.application.data_path = user_dir

    async def create_pipeline_async(self, user_id: str) -> Pipeline:
        if user_id in self.pipelines:
            logger.info(f"Returning existing pipeline for user {user_id}")
            return self.pipelines[user_id]

        logger.info(f"Creating new pipeline for user {user_id}")
        if self.is_api_server:
            await self.override_user_data_path(user_id)
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
        if user_id not in self.pipelines:
            if self.is_api_server:
                await self.override_user_data_path(user_id)
            pipeline = Pipeline(self.config.copy())
            await pipeline.setup()
            self.pipelines[user_id] = pipeline
        return self.pipelines[user_id]

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

# TODO :: Move embed model per user to docker setting to avoid reinitializing same model for every user
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
