from typing import List, Tuple, Optional
from collections import OrderedDict
from llamasearch.logger import logger
from llamasearch.latency import track_latency

import torch
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
        self.multi_tenancy = getattr(self.vectordb_config, 'multi_tenancy', False)
        logger.info(f"Multi tenancy: {self.multi_tenancy}")

    async def setup_index_async(self, tenant_id=None):
        """Set up the Qdrant index for hybrid search asynchronously."""
        try:
            await self.initialize_qdrant_client_async()
            await self.create_collection_async()
            await self.create_vector_store_async(tenant_id=tenant_id)
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

    async def create_collection_async(self):
        """Recreate the Qdrant collection with specified configuration asynchronously."""
        try:
            collections = await self.aclient.get_collections()
            collection_names = [collection.name for collection in collections.collections]
            logger.debug(f"Collection names: {collection_names}")
            if self.vectordb_config.collection_name not in collection_names:
                logger.info("Collection {} does not exist. Creating new collection...".format(self.vectordb_config.collection_name))
                await self.aclient.create_collection(
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
                # One downside to this approach is that global requests (without the group_id filter) will be slower
                # since they will necessitate scanning all groups to identify the nearest neighbors. (From doc)
                if self.multi_tenancy:
                    # Update HNSW configuration for better performance in multitenant scenarios (global searches would be slower)
                    await self.aclient.update_collection(
                        collection_name=self.vectordb_config.collection_name,
                        hnsw_config=models.HnswConfigDiff(payload_m=16, m=0),
                    )

            if self.multi_tenancy:
                await self.aclient.create_payload_index(
                    collection_name=self.vectordb_config.collection_name,
                    field_name="tenant_id",
                    field_schema=models.PayloadSchemaType.KEYWORD,
                )
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            raise
    
    @track_latency
    async def create_vector_store_async(self, collection_name=None, tenant_id=None):
        try:
            #Assign default name if not specified
            if collection_name is None:
                collection_name = self.vectordb_config.collection_name
            print(f"Creating vector store for collection {collection_name}")
            vector_store_config = {
                "collection_name": collection_name,
                "client": self.client,
                "aclient": self.aclient,
                "enable_hybrid": True,
                "batch_size": self.vectordb_config.batch_size,
                "hybrid_fusion_fn": self.relative_score_fusion,
            }
            if self.multi_tenancy and tenant_id:
                vector_store_config.update({
                    "metadata_payload_key": "tenant_id" if tenant_id else None
                })
            self.vector_store = QdrantVectorStore(**vector_store_config)
        except Exception as e:
            logger.error(f"Error creating QdrantVectorStore: {e}")
            raise

    @track_latency
    async def create_index_async(self):
        """Create a vector store index from given nodes and docstore asynchronously."""
        self.index = VectorStoreIndex.from_vector_store(
            self.vector_store,
            Settings.embed_model,
            store_nodes_override=True
        )

    @track_latency
    async def add_nodes_to_index_async(self, nodes, tenant_id=None):
        logger.info("Adding nodes to index...")
        if self.multi_tenancy and tenant_id:
            for node in nodes:
                node.metadata["tenant_id"] = tenant_id
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
        try:
            alpha = alpha or self.vectordb_config.alpha
            top_k = top_k or self.vectordb_config.topk

            # Quick return for empty results
            if not dense_result.nodes and not sparse_result.nodes:
                logger.warning("Both dense and sparse results are empty")
                return VectorStoreQueryResult(nodes=[], similarities=[], ids=[])

            # Prepare data structures
            fused_scores = {}
            all_nodes = {}

            # Process dense results
            if dense_result.nodes:
                dense_max = max(dense_result.similarities)
                dense_min = min(dense_result.similarities)
                dense_range = dense_max - dense_min or 1  # Avoid division by zero

                for node, sim in zip(dense_result.nodes, dense_result.similarities):
                    normalized_sim = (sim - dense_min) / dense_range
                    fused_scores[node.node_id] = alpha * normalized_sim
                    all_nodes[node.node_id] = node

            # Process sparse results
            if sparse_result.nodes:
                sparse_max = max(sparse_result.similarities)
                sparse_min = min(sparse_result.similarities)
                sparse_range = sparse_max - sparse_min or 1  # Avoid division by zero

                for node, sim in zip(sparse_result.nodes, sparse_result.similarities):
                    normalized_sim = (sim - sparse_min) / sparse_range
                    fused_scores[node.node_id] = fused_scores.get(node.node_id, 0) + alpha * normalized_sim
                    all_nodes[node.node_id] = node

            # Sort and limit results
            sorted_results = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

            # Create final response object
            return VectorStoreQueryResult(
                nodes=[all_nodes[node_id] for node_id, _ in sorted_results],
                similarities=[score for _, score in sorted_results],
                ids=[node_id for node_id, _ in sorted_results]
            )

        except Exception as e:
            logger.error(f"Error in relative_score_fusion: {str(e)}", exc_info=True)
            return VectorStoreQueryResult(nodes=[], similarities=[], ids=[])

    # def get_nodes(self, limit=None):
    #     print(self.index.ref_doc_info)
    #     nodes = self.index.docstore.docs
    #     if limit is not None:
    #         limited_nodes = OrderedDict(list(nodes.items())[:limit])
    #         return limited_nodes.values()
    #     return nodes.values()

    async def delete_nodes(self, node_ids: List[str]):
        await self.aclient.delete(
            collection_name=self.vectordb_config.collection_name,
            points_selector=models.PointIdsList(points=node_ids)
        )
        logger.info(f"Deleted {len(node_ids)} nodes from Qdrant")


    async def cleanup(self):
        if self._client:
            self._client.close()
        if self._aclient:
            await self._aclient.close()
        self._client = None
        self._aclient = None