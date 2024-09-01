
from typing import Any, List, Tuple, Dict, Optional
from tabulate import tabulate
import asyncio
import os
import json
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
from qdrant_client import models

from llamasearch.Ragflow import RagflowNodeParser




documents = SimpleDirectoryReader("./data/test").load_data()


parser=SentenceSplitter(chunk_size=512, chunk_overlap=10)

nodes=parser.get_nodes_from_documents(documents=documents)
rsult={}
for i in range(len(nodes)):
    rsult[f'node_{i}']=nodes[i].get_content()
with open('parser-data_splitter.json', 'w') as fp:
    json.dump(rsult, fp,indent=4)