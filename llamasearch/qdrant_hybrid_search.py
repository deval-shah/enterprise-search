from typing import List, Tuple, Optional
from collections import OrderedDict
import torch
import asyncio

from llamasearch.logger import logger
from llamasearch.latency import track_latency

from qdrant_client import QdrantClient, AsyncQdrantClient, models
from transformers import AutoTokenizer, AutoModelForMaskedLM
from llama_index.core.vector_stores import VectorStoreQueryResult
from llama_index.core import  VectorStoreIndex, Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore

class QdrantHybridSearch:
    """Manages Qdrant vector store operations for hybrid search."""
    def __init__(self, config):
        self.latency_profile = {}
        self.vector_store = None
        self.index = None
        self.vectordb_config = config.vector_store_config
        self.vectordb_client_config = config.qdrant_client_config
        self._client = None
        self._aclient = None

    async def setup_index_async(self):
        """Set up the Qdrant index for hybrid search asynchronously."""
        try:
            await self.initialize_qdrant_client_async()
            await self.recreate_collection_async()
            await self.create_vector_store_async()
        except Exception as e:
            logger.error(f"Error: {e}")

    async def initialize_qdrant_client_async(self):
        """Initialize the Qdrant client connection asynchronously."""
        try:
            self._aclient = AsyncQdrantClient(
                url=self.vectordb_client_config.url,
                prefer_grpc=self.vectordb_client_config.prefer_grpc
            )
            self._client = QdrantClient(
                url=self.vectordb_client_config.url,
                prefer_grpc=self.vectordb_client_config.prefer_grpc
            )
        except Exception as e:
            logger.error(f"Error connecting to Qdrant: {e}")
            raise
    
    @property
    def client(self):
        if self._client is None:
            raise ValueError("Qdrant client has not been initialized. Call initialize_qdrant_client_async first.")
        return self._client

    @property
    def aclient(self):
        if self._aclient is None:
            raise ValueError("Async Qdrant client has not been initialized. Call initialize_qdrant_client_async first.")
        return self._aclient

    async def recreate_collection_async(self):
        """Recreate the Qdrant collection with specified configuration asynchronously."""
        try:
            await self.aclient.recreate_collection(
                collection_name=self.vectordb_config.collection_name,
                vectors_config={
                    "text-dense": models.VectorParams(
                        size=self.vectordb_config.vector_size,
                        distance=self.vectordb_config.distance,
                    )
                },
                sparse_vectors_config={
                    "text-sparse": models.SparseVectorParams(
                        index=models.SparseIndexParams()
                    )
                },
                )
        except Exception as e:
            logger.error(f"Error recreating collection: {e}")
            raise
    
    @track_latency
    async def create_vector_store_async(self, collection_name=None):
        try:
            #Assign default name if not specified
            if collection_name is None:
                collection_name = self.vectordb_config.collection_name
            print(f"Creating vector store for collection {collection_name}")
            self.vector_store = QdrantVectorStore(
                collection_name=collection_name,
                # client=self._client,
                aclient=self._aclient,
                enable_hybrid=True,
                batch_size=self.vectordb_config.batch_size,
                hybrid_fusion_fn=self.relative_score_fusion
            )
        except Exception as e:
            logger.error(f"Error creating QdrantVectorStore: {e}")
            raise
        
    @track_latency
    async def create_index_async(self):
        """Create a vector store index from given nodes and docstore asynchronously."""
        self.index = VectorStoreIndex.from_vector_store(
            self.vector_store,
            Settings.embed_model,
            store_nodes_override = True
        )

    @track_latency
    async def add_nodes_to_index_async(self, nodes):
        await self.index._async_add_nodes_to_index(
            self.index.index_struct,
            nodes,
            show_progress = True
        )

    def sparse_doc_vectors(
        self,
        texts: List[str],
    ) -> Tuple[List[List[int]], List[List[float]]]:
        """
        Computes vectors from logits and attention mask using ReLU, log, and max operations.
        """
        doc_tokenizer = AutoTokenizer.from_pretrained(
            "naver/efficient-splade-VI-BT-large-doc"
)
        doc_model = AutoModelForMaskedLM.from_pretrained(
            "naver/efficient-splade-VI-BT-large-doc"
        )
        tokens = doc_tokenizer(
            texts, truncation=True, padding=True, return_tensors="pt"
        )
        if torch.cuda.is_available():
            tokens = tokens.to("cuda")

        output = doc_model(**tokens)
        logits, attention_mask = output.logits, tokens.attention_mask
        relu_log = torch.log(1 + torch.relu(logits))
        weighted_log = relu_log * attention_mask.unsqueeze(-1)
        tvecs, _ = torch.max(weighted_log, dim=1)

        # extract the vectors that are non-zero and their indices
        indices = []
        vecs = []
        for batch in tvecs:
            indices.append(batch.nonzero(as_tuple=True)[0].tolist())
            vecs.append(batch[indices[-1]].tolist())

        return indices, vecs

    def sparse_query_vectors(
        self,
        texts: List[str],
    ) -> Tuple[List[List[int]], List[List[float]]]:
        """
        Computes vectors from logits and attention mask using ReLU, log, and max operations.
        """
        query_tokenizer = AutoTokenizer.from_pretrained(
            "naver/efficient-splade-VI-BT-large-query"
        )
        query_model = AutoModelForMaskedLM.from_pretrained(
            "naver/efficient-splade-VI-BT-large-query"
        )
        # TODO: compute sparse vectors in batches if max length is exceeded
        tokens = query_tokenizer(
            texts, truncation=True, padding=True, return_tensors="pt"
        )
        if torch.cuda.is_available():
            tokens = tokens.to("cuda")

        output = query_model(**tokens)
        logits, attention_mask = output.logits, tokens.attention_mask
        relu_log = torch.log(1 + torch.relu(logits))
        weighted_log = relu_log * attention_mask.unsqueeze(-1)
        tvecs, _ = torch.max(weighted_log, dim=1)

        # extract the vectors that are non-zero and their indices
        indices = []
        vecs = []
        for batch in tvecs:
            indices.append(batch.nonzero(as_tuple=True)[0].tolist())
            vecs.append(batch[indices[-1]].tolist())

        return indices, vecs

    @track_latency
    def relative_score_fusion(
        self,
        dense_result: VectorStoreQueryResult,
        sparse_result: VectorStoreQueryResult,
        alpha: Optional[float] = None,
        top_k: Optional[int] = None,
    ) -> VectorStoreQueryResult:
        alpha = alpha or self.vectordb_config.alpha
        top_k = top_k or self.vectordb_config.topk
        """Fuse dense and sparse search results using relative score fusion."""
        # sanity check
        assert dense_result.nodes is not None
        assert dense_result.similarities is not None
        assert sparse_result.nodes is not None
        assert sparse_result.similarities is not None

        # deconstruct results
        sparse_result_tuples = list(
            zip(sparse_result.similarities, sparse_result.nodes)
        )
        sparse_result_tuples.sort(key=lambda x: x[0], reverse=True)

        dense_result_tuples = list(
            zip(dense_result.similarities, dense_result.nodes)
        )
        dense_result_tuples.sort(key=lambda x: x[0], reverse=True)

        # track nodes in both results
        all_nodes_dict = {x.node_id: x for x in dense_result.nodes}
        for node in sparse_result.nodes:
            if node.node_id not in all_nodes_dict:
                all_nodes_dict[node.node_id] = node

        # normalize sparse similarities from 0 to 1
        sparse_similarities = [x[0] for x in sparse_result_tuples]
        max_sparse_sim = max(sparse_similarities)
        min_sparse_sim = min(sparse_similarities)
        sparse_similarities = [
            (x - min_sparse_sim) / (max_sparse_sim - min_sparse_sim)
            for x in sparse_similarities
        ]
        sparse_per_node = {
            sparse_result_tuples[i][1].node_id: x
            for i, x in enumerate(sparse_similarities)
        }

        # normalize dense similarities from 0 to 1
        dense_similarities = [x[0] for x in dense_result_tuples]
        max_dense_sim = max(dense_similarities)
        min_dense_sim = min(dense_similarities)
        dense_similarities = [
            (x - min_dense_sim) / (max_dense_sim - min_dense_sim)
            for x in dense_similarities
        ]
        dense_per_node = {
            dense_result_tuples[i][1].node_id: x
            for i, x in enumerate(dense_similarities)
        }

        # fuse the scores
        fused_similarities = []
        for node_id in all_nodes_dict:
            sparse_sim = sparse_per_node.get(node_id, 0)
            dense_sim = dense_per_node.get(node_id, 0)
            fused_sim = alpha * (sparse_sim + dense_sim)
            fused_similarities.append((fused_sim, all_nodes_dict[node_id]))

        fused_similarities.sort(key=lambda x: x[0], reverse=True)
        fused_similarities = fused_similarities[:top_k]

        # create final response object
        return VectorStoreQueryResult(
            nodes=[x[1] for x in fused_similarities],
            similarities=[x[0] for x in fused_similarities],
            ids=[x[1].node_id for x in fused_similarities],
        )

    def get_nodes(self, limit=None):
        nodes = self.index.docstore.docs
        if limit is not None:
            limited_nodes = OrderedDict(list(nodes.items())[:limit])
            return limited_nodes.values()
        return nodes.values()

    def cleanup(self):
        if self._client:
            self._client.close()
        if self._aclient:
            asyncio.create_task(self._aclient.close())
        self._client = None
        self._aclient = None