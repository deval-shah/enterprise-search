from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.core.extractors import TitleExtractor
from llama_index.core.ingestion import IngestionPipeline, IngestionCache
from llama_index.storage.kvstore.redis import RedisKVStore as RedisCache
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import Settings
from llama_index.core.embeddings import resolve_embed_model
from llama_index.llms.ollama import Ollama
from llama_index.storage.docstore.redis import RedisDocumentStore
from llama_index.core.base.response.schema import Response
from logger import CustomLogger

import yaml
import logging
import qdrant_client
from utils import profile_
import argparse
import os
import asyncio
from typing import Optional
from docxreader import DocxReader

logger = CustomLogger.setup_logger(__name__, save_to_disk=True, log_dir='/data/app/logs/', log_name='pipeline.log')

class LlamaIndexApp:
    """
    A class to encapsulate the application logic for indexing and querying documents using LLaMA index.
    """
    def __init__(self, config_path: str):
        """
        Initializes the application with the provided configuration.

        Args:
            config_path (str): The path to the YAML configuration file.
        """
        logger.info("Initializing RAG pipeline with provided configuration {}.".format(config_path))
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        self.data_path = config['data_path']
        self.qdrant_client_config = config['qdrant_client_config']
        self.vector_store_config = config['vector_store_config']
        self.redis_config = config['redis_config']
        self.embed_model = config['embed_model']
        self.llm_model = config['llm_model']
        self.setup()

    def setup(self):
        """
        Sets up the application components including embedding model, vector store, cache, and ingestion pipeline.
        """
        self.setup_embed_model()
        self.setup_llm()
        self.setup_vector_store()
        self.setup_cache()
        self.setup_pipeline()

    def setup_embed_model(self):
        """Initializes the embedding model based on the configuration."""
        Settings.embed_model = resolve_embed_model(self.embed_model)

    def setup_llm(self):
        """Initializes the Large Language Model (LLM) based on the configuration."""
        Settings.llm = Ollama(model=self.llm_model, request_timeout=30.0)

    def setup_vector_store(self):
        """Initializes the vector store client and vector store based on the configuration."""
        # To work with local vector store, update url in config
        # self.qdrant_client_config['location'] = ':memory:'
        try:
            logger.info("Setting up the Vector store ....")
            self.client = qdrant_client.QdrantClient(**self.qdrant_client_config)
            self.vector_store = QdrantVectorStore(client=self.client, **self.vector_store_config)
        except Exception as e:
            logging.error(f"Failed to initialize the vector store: {e}")
            raise PipelineSetupError("Failed to initialize the vector store") from e

    def setup_cache(self):
        """Initializes the ingestion cache using Redis for storing intermediate results."""
        try:
            logger.info("Setting up the Ingestion Cache ....")
            self.cache = IngestionCache(cache=RedisCache.from_host_and_port(**self.redis_config), collection="redis_cache")
        except Exception as e:
            logging.error(f"Failed to initialize Ingestion Redis cache: {e}")
            raise PipelineSetupError("Failed to setup initialize Ingestion Redis cache.") from e

    def setup_pipeline(self):
        """
        Initializes the ingestion pipeline with specified transformations and stores.
        """
        try:
            logger.info("Setting up the Ingestion pipeline....")
            self.pipeline = IngestionPipeline(
                transformations=[
                    SemanticSplitterNodeParser(buffer_size=3, breakpoint_percentile_threshold=95, embed_model=Settings.embed_model),
                    #SentenceSplitter(chunk_size=1024, chunk_overlap=20),
                    #TitleExtractor(num_workers=8),
                    Settings.embed_model,
                ],
                vector_store=self.vector_store,
                cache=self.cache,
                docstore=RedisDocumentStore.from_host_and_port(**self.redis_config, namespace="document_store"),
            )
        except Exception as e:
            logger.error(f"Failed to setup ingestion pipeline: {e}")
            raise PipelineSetupError("Failed to setup pipeline.") from e

    @profile_
    async def load_documents(self):
        """Loads documents from the specified directory for indexing."""
        logger.info("Loading documents from the specified directory for indexing.")
        self.documents = SimpleDirectoryReader(self.data_path, recursive=False, filename_as_id=True, file_extractor={".docx":DocxReader()}).load_data()

    @profile_
    async def run_pipeline(self):
        """
        Processes the loaded documents through the ingestion pipeline.

        Returns:
            List: A list of processed document nodes.
        """
        logger.info("Generating nodes from ingested documents")
        nodes = self.pipeline.run(documents=self.documents)
        logger.info(f"Ingested {len(nodes)} Nodes")
        return nodes

    @profile_
    async def index_documents(self, nodes):
        """Indexes the processed documents."""
        logger.info("Indexing processed documents.")
        self.index = VectorStoreIndex.from_vector_store(self.vector_store, Settings.embed_model)
        logger.info("Initialising the query engine...")
        self.set_query_engine()
        
    def set_query_engine(self):
        if not hasattr(self, 'index') or self.index is None:
            raise Exception("Index is not ready. Please load and index documents before querying.")
        self.query_engine = self.index.as_query_engine()
 
    @profile_
    async def query_engine_response(self, query):
        """
        Queries the index with the given query string.

        Args:
            query (str): The query string.

        Returns:
            dict: The query response.
        """
        response = None
        try:
            logger.info("Calling query engine...")
            response = self.query_engine.query(query)
        except Exception as e:
            logger.error(f"An error occurred in the query engine call: {str(e)}")
            os._exit(1)
        return response

    def get_context_from_response(self, response_object):
        # Process the response object to get the output string and retrieved nodes
        if response_object is not None:
            actual_output = response_object.response
            retrieval_context = [node.get_content() for node in response.source_nodes]
        return {"output": actual_output, "retrieval_context": retrieval_context}

@profile_
async def query_app(config_path: str, query: str, data_path: Optional[str] = None):
    """
    Loads documents, runs the ingestion pipeline, indexes documents, and queries the index.

    Args:
        config_path: The path to the configuration file.
        query: The query string to search the index.
        data_path: Optional; The path to the data directory. If provided, overrides the default path.
    """
    try:
        app = LlamaIndexApp(config_path)
        if data_path:
            app.data_path = data_path
        await app.load_documents()
        nodes = await app.run_pipeline()
        await app.index_documents(nodes)
        response = await app.query_engine_response(query)
        logger.info("Response : {}".format(response))
        return response
    except Exception as e:
        logger.error(f"An error occurred in query app fn: {str(e)}")

# Custom exception for pipeline setup errors
class PipelineSetupError(Exception):
    """Exception raised for errors during the setup of the ingestion pipeline."""
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query the LlamaIndexApp")
    parser.add_argument("--query", type=str, help="Query string to search the index with", required=True)
    args = parser.parse_args()
    config_path = 'config.yml'
 
    logger.info("Starting the RAG pipeline...")
    try:
        response = asyncio.run(query_app(config_path, args.query))
        logger.info(f"Response: {response}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
