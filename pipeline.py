from llama_index.core import Document,  VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter, SemanticSplitterNodeParser
from llama_index.core.extractors import TitleExtractor
from llama_index.core.ingestion import IngestionPipeline, IngestionCache
from llama_index.storage.kvstore.redis import RedisKVStore as RedisCache
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import Settings
from llama_index.core import VectorStoreIndex
from llama_index.core.embeddings import resolve_embed_model
from llama_index.llms.ollama import Ollama
from llama_index.storage.docstore.redis import RedisDocumentStore

import yaml
import logging
import sys
import qdrant_client
import cProfile
import pstats
import argparse
from typing import Optional, Dict

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

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
        self.client = qdrant_client.QdrantClient(**self.qdrant_client_config)
        self.vector_store = QdrantVectorStore(client=self.client, **self.vector_store_config)

    def setup_cache(self):
        """Initializes the ingestion cache using Redis for storing intermediate results."""
        self.cache = IngestionCache(cache=RedisCache.from_host_and_port(**self.redis_config), collection="redis_cache")

    def setup_pipeline(self):
        """
        Initializes the ingestion pipeline with specified transformations and stores.
        """
        self.pipeline = IngestionPipeline(
            transformations=[
                SemanticSplitterNodeParser(buffer_size=3, breakpoint_percentile_threshold=95, embed_model=Settings.embed_model),
                #SentenceSplitter(chunk_size=1024, chunk_overlap=20),
                TitleExtractor(num_workers=8),
                Settings.embed_model,
            ],
            vector_store=self.vector_store,
            cache=self.cache,
            docstore=RedisDocumentStore.from_host_and_port(**self.redis_config, namespace="document_store"),
        )

    def load_documents(self):
        """Loads documents from the specified directory for indexing."""
        self.documents = SimpleDirectoryReader(self.data_path, recursive=True, filename_as_id=True).load_data()
        print(self.documents)

    def run_pipeline(self):
        """
        Processes the loaded documents through the ingestion pipeline.

        Returns:
            List: A list of processed document nodes.
        """
        nodes = self.pipeline.run(documents=self.documents, show_progress=True)
        print(f"Ingested {len(nodes)} Nodes")
        return nodes

    def index_documents(self, nodes):
        """Indexes the processed documents."""
        self.index = VectorStoreIndex.from_vector_store(self.vector_store, Settings.embed_model)

    def query_index(self, query):
        """
        Queries the index with the given query string.

        Args:
            query (str): The query string.

        Returns:
            dict: The query response.
        """
        query_engine = self.index.as_query_engine(similarity_top_k=10)
        response = query_engine.query(query)
        return response

def query_app(config_path: str, query: str, data_path: Optional[str] = None) -> Dict:
    """
    Queries the application with a specified query string after loading documents,
    running the pipeline, and indexing documents.

    Args:
        config_path (str): Path to the YAML configuration file.
        query (str): The query string to search the index with.
        data_path (Optional[str]): Optional. Custom path to override the data path specified in the config.

    Returns:
        String: The response from querying the index using LLM.
    """
    app = LlamaIndexApp(config_path)
    if data_path:
        app.data_path = data_path
    app.load_documents()
    nodes = app.run_pipeline()
    app.index_documents(nodes)
    response = app.query_index(query)
    return response

def profile_app(config_path: str, query: str) -> None:
    """
    Profiles the application's performance during the execution of a query.

    Args:
        config_path (str): Path to the YAML configuration file.
        query (str): The query string to search the index with.
    """
    profiler = cProfile.Profile()
    profiler.enable()
    query_app(config_path, query)
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('cumulative')
    stats.print_stats(10)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Profile or Query the LlamaIndexApp")
    parser.add_argument("--query", type=str, help="Query string to search the index with", required=True)
    parser.add_argument("--profile", action='store_true', help="Enable profiling of the app")
    args = parser.parse_args()
    config_path='config.yml'
    try:
        if args.profile:
            profile_app(config_path, args.query)
        else:
            response = query_app(config_path, args.query)
            logging.info(f"Response: {response}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")