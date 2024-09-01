import argparse
import asyncio
import os
from typing import Optional

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core import Settings
from llama_index.core import PromptTemplate
from llama_index.core.embeddings import resolve_embed_model
from llama_index.core.ingestion import IngestionPipeline, IngestionCache
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.ollama import Ollama
from llama_index.postprocessor.flag_embedding_reranker import (
    FlagEmbeddingReranker,
)
from llama_index.storage.docstore.redis import RedisDocumentStore
from llama_index.storage.kvstore.redis import RedisKVStore as RedisCache
from llama_index.vector_stores.qdrant import QdrantVectorStore
import qdrant_client

from llamasearch.logger import logger
from llamasearch.utils import profile_, load_yaml_file
from llamasearch.settings import config
from llamasearch.pubspdfreader import PubsPDFReader

class LlamaIndexApp:
    """
    A class to encapsulate the application logic for indexing and querying documents using LLaMA index.
    """
    def __init__(self):
        """
        Initializes the application with the provided configuration.
        """
        self.config = config
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
        self.setup_reranker()

    def setup_embed_model(self):
        """Initializes the embedding model based on the configuration."""
        Settings.embed_model = resolve_embed_model(self.config.embedding.model)

    def setup_llm(self):
        """Initializes the Large Language Model (LLM) based on the configuration."""
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

    def setup_vector_store(self):
        """Initializes the vector store client and vector store based on the configuration."""
        try:
            logger.debug(f"Initializing Qdrant Client with config: URL={self.config.qdrant_client_config}")
            self.client = qdrant_client.QdrantClient(
                url=self.config.qdrant_client_config.url,
                prefer_grpc=self.config.qdrant_client_config.prefer_grpc
            )
            logger.debug(f"Initializing vector store with config: URL={self.config.vector_store_config}")
            self.vector_store = QdrantVectorStore(client=self.client,
                                                  collection_name=self.config.vector_store_config.collection_name,
                                                  vector_size=self.config.vector_store_config.vector_size,
                                                  distance=self.config.vector_store_config.distance,
                                                  max_optimization_threads=1)
        except Exception as e:
            logger.error(f"Failed to initialize the vector store: {e}")
            raise PipelineSetupError("Failed to initialize the vector store") from e

    def setup_reranker(self, top_n=5):
        self.reranker = FlagEmbeddingReranker(
            top_n=top_n,
            model=self.config.reranker.model,
        )

    def setup_cache(self):
        """Initializes the ingestion cache using Redis for storing intermediate results."""
        try:
            logger.info("Setting up the Ingestion Cache ....")
            self.cache = IngestionCache(cache=RedisCache.from_host_and_port(host=self.config.redis_config.host, port=self.config.redis_config.port), collection="redis_cache")
        except Exception as e:
            logger.error(f"Failed to initialize Ingestion Redis cache: {e}")
            raise PipelineSetupError("Failed to setup initialize Ingestion Redis cache.") from e

    def setup_pipeline(self):
        """
        Initializes the ingestion pipeline with specified transformations and stores.
        """
        try:
            logger.info("Setting up the Ingestion pipeline....")
            self.pipeline = IngestionPipeline(
                transformations=[
                    SentenceSplitter(chunk_size=512, chunk_overlap=25),
                    Settings.embed_model,
                ],
                vector_store=self.vector_store,
                cache=self.cache,
                docstore=RedisDocumentStore.from_host_and_port(host=self.config.redis_config.host, port=self.config.redis_config.port, namespace="document_store"),
            )
        except Exception as e:
            logger.error(f"Failed to setup ingestion pipeline: {e}")
            raise PipelineSetupError("Failed to setup pipeline.") from e

    @profile_
    async def load_documents(self):
        """Loads documents from the specified directory for indexing."""
        logger.info("Loading documents from the specified directory for indexing.")
        allowed_exts = [".pdf"]
        self.documents = SimpleDirectoryReader(self.data_path, recursive=True, filename_as_id=True, required_exts=allowed_exts, file_extractor={".pdf": PubsPDFReader()}).load_data()

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
        logger.debug("Indexing processed documents.")
        self.index = VectorStoreIndex.from_vector_store(self.vector_store, Settings.embed_model)
        self.set_query_engine()

    def set_query_engine(self):
        if not hasattr(self, 'index') or self.index is None:
            raise Exception("Index is not ready. Please load and index documents before querying.")
        self.query_engine = self.index.as_query_engine(similarity_top_k=30, node_postprocessors=[self.reranker])

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
        return PromptTemplate(template)

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
            logger.debug("Calling query engine...")
            qa_template = self.update_prompt()
            self.query_engine.update_prompts(
                {"response_synthesizer:text_qa_template": qa_template}
            )
            response = self.query_engine.query(query)
        except Exception as e:
            logger.error(f"An error occurred in the query engine call: {str(e)}")
            os._exit(1)
        return response

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
                    file_path = info.get('file_path')
                    if file_path and file_path not in document_info:
                        document_info[file_path] = {
                            'file_name': info.get('file_name'),
                            'last_modified_date': info.get('last_modified_date'),
                            'doc_id': doc_id
                        }
        except Exception as e:
            logger.error(f"An error occurred while processing the response object: {e}")
    return document_info, retrieval_context

@profile_
async def query_app(query: str, data_path: Optional[str] = None, no_ingest: bool = False):
    """
    Loads documents, runs the ingestion pipeline, indexes documents, and queries the index.

    Args:
        query: The query string to search the index.
        data_path: Optional; The path to the data directory. If provided, overrides the default path.
    """
    try:
        logger.info("Initializing the pipeline...")
        app = LlamaIndexApp()
        if data_path:
            app.data_path = data_path
        if no_ingest:
            await app.index_documents([])
        else:
            await app.load_documents()
            nodes = await app.run_pipeline()
            await app.index_documents(nodes)
        return await app.query_engine_response(query)
    except Exception as e:
        logger.error(f"An error occurred in query app fn: {str(e)}")

# Custom exception for pipeline setup errors
class PipelineSetupError(Exception):
    """Exception raised for errors during the setup of the ingestion pipeline."""
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ES pipeline")
    parser.add_argument("--query", type=str, help="Query text to ask question on the data", required=True)
    parser.add_argument("--data_path", type=str, help="Knowledge base folder path", default='./data/test', required=False)
    parser.add_argument("--context", help="Flag to display retrieved context", action="store_true")
    parser.add_argument("--no_ingest", help="Flag to disable ingest", action="store_true")
    args = parser.parse_args()

    logger.info("Starting the pipeline...")
    try:
        response = asyncio.run(query_app(args.query, args.data_path, args.no_ingest))
        logger.info(f"Response: {response}")
        if args.context:
            document_info, retrieval_context = get_context_from_response(response)
            context_details = '\n'.join(["File Path: {}, File Name: {}, Last Modified: {}, Document ID: {}".format(
                path, details['file_name'], details['last_modified_date'], details['doc_id']) for path, details in document_info.items()])
            logger.info('\n' + '=' * 60 + '\nDocument Context Information\n' + context_details + '\n' + '=' * 60)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
