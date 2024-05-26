from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.core.extractors import TitleExtractor
from llama_index.core.ingestion import IngestionPipeline, IngestionCache
from llama_index.storage.kvstore.redis import RedisKVStore as RedisCache
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import Settings
from llama_index.core.embeddings import resolve_embed_model
from llama_index.llms.ollama import Ollama
from llama_index.core import PromptTemplate
from llama_index.storage.docstore.redis import RedisDocumentStore
import argparse
import os
import asyncio
import qdrant_client
from src.logger import logger
from src.utils import profile_
from typing import Optional
from src.docxreader import DocxReader
from src.settings import config

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

    def setup_embed_model(self):
        """Initializes the embedding model based on the configuration."""
        Settings.embed_model = resolve_embed_model(self.config.embedding.embed_model)

    def setup_llm(self):
        """Initializes the Large Language Model (LLM) based on the configuration."""
        base_url = os.getenv('OLLAMA_SERVER_URL', 'http://localhost:11434')
        logger.info(f"Running model {self.config.llm.llm_model} on URL : {base_url}")
        Settings.llm = Ollama(
                      base_url=base_url,
                      model=self.config.llm.llm_model,
                      temperature=0.7,
                      additional_kwargs={"num_predict": 128, "num_ctx": 2048},
                      request_timeout=30.0
                    )

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
                    SemanticSplitterNodeParser(buffer_size=3, breakpoint_percentile_threshold=95, embed_model=Settings.embed_model),
                    #SentenceSplitter(chunk_size=1024, chunk_overlap=20),
                    #TitleExtractor(num_workers=8),
                    Settings.embed_model,
                ],
                vector_store=self.vector_store,
                cache=self.cache,
                docstore=RedisDocumentStore.from_host_and_port(host=self.config.redis_config.host, port=self.config.redis_config.port, namespace="document_store"),
            )
        except Exception as e:
            logger.error(f"Failed to setup ingestion pipeline: {e}")
            raise PipelineSetupError("Failed to setup pipeline.") from e

    #@profile_
    async def load_documents(self):
        """Loads documents from the specified directory for indexing."""
        logger.info("Loading documents from the specified directory for indexing.")
        allowed_exts = [".pdf", ".docx", ".txt"]
        self.documents = SimpleDirectoryReader(self.data_path, recursive=False, filename_as_id=True, required_exts=allowed_exts, file_extractor={".docx":DocxReader()}).load_data()

    #@profile_
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

    #@profile_
    async def index_documents(self, nodes):
        """Indexes the processed documents."""
        logger.debug("Indexing processed documents.")
        self.index = VectorStoreIndex.from_vector_store(self.vector_store, Settings.embed_model)
        self.set_query_engine()
        
    def set_query_engine(self):
        if not hasattr(self, 'index') or self.index is None:
            raise Exception("Index is not ready. Please load and index documents before querying.")
        self.query_engine = self.index.as_query_engine()

    def update_prompt(self):
        template = (
            "\n"
            "[INST] You are an AI trained to accurately use detailed context to answer questions. Follow these guidelines: \n"
            "- Use the provided context information from the document below to answer the question. \n"
            "- Your answer should be short, concise and grounded in the document's facts,  \n"
            "- If the provided context does not contain sufficient facts to answer the question, respond with: 'I am unable to answer based on the given context information.' \n"
            "[/INST]\n"
            "\n"
            "{context_str}\n"
            "---------------------\n"
            "Based on the above context, please answer the question: {query_str}. Strictly follow guidelines\n"
        )
        qa_template = PromptTemplate(template)
        return qa_template

    #@profile_
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

    Iterating over each document's information. It compiles a dictionary of unique file paths with their respective details and logs a formatted
    summary of these details and maps it to the response. Useful for citing the source.
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
            logger.error("An error occurred while processing the response object: {}".format(e))
    return document_info, retrieval_context

@profile_
async def query_app(query: str, data_path: Optional[str] = None):
    """
    Loads documents, runs the ingestion pipeline, indexes documents, and queries the index.

    Args:
        query: The query string to search the index.
        data_path: Optional; The path to the data directory. If provided, overrides the default path.
    """
    try:
        logger.info(f"Initializing the pipeline...")
        app = LlamaIndexApp()
        if data_path:
            app.data_path = data_path
        await app.load_documents()
        nodes = await app.run_pipeline()
        await app.index_documents(nodes)
        response = await app.query_engine_response(query)
        return response
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
    args = parser.parse_args()

    logger.info("Starting the pipeline...")
    try:
        response = asyncio.run(query_app(args.query, args.data_path))
        logger.info(f"Response: {response}")
        document_info, retrieval_context = get_context_from_response(response)
        context_details = '\n'.join(["File Path: {}, File Name: {}, Last Modified: {}, Document ID: {}".format(
            path, details['file_name'], details['last_modified_date'], details['doc_id']) for path, details in document_info.items()])
        logger.debug('\n' + '=' * 60 + '\nDocument Context Information\n' + context_details + '\n' + '=' * 60)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
