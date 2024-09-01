from llamasearch.pipeline import Pipeline

from llamasearch.pipeline import PipelineFactory
from llamasearch.settings import config
import asyncio
from llama_index.postprocessor.flag_embedding_reranker import (
    FlagEmbeddingReranker,
)
from llamasearch.qdrant_hybrid_search import QdrantHybridSearch
async def main():
    reranker = FlagEmbeddingReranker(
            top_n=config.reranker.top_n,
            model=config.reranker.model,
        )
    factory = PipelineFactory()
    user_id = "123456"
    tenant_id = "tenant1"
    pipeline =  await factory.get_or_create_pipeline_async(user_id, tenant_id)
    
    try:
        print(pipeline.is_setup_complete)
        top_k = config.vector_store_config.top_k
        enable_hybrid = config.vector_store_config.enable_hybrid
        query_engine_kwargs = {
            "node_postprocessors": [reranker],
            "similarity_top_k": top_k,
            "response_mode":"compact"
        }
        if enable_hybrid:
        # logger.debug("Hybrid search is enabled...")
            query_engine_kwargs["vector_store_query_mode"] = "hybrid"
        
    # if self.multi_tenancy and qdrant_filters:
    #         query_engine_kwargs["vector_store_kwargs"] = {"qdrant_filters": qdrant_filters}
        qdrant_search = QdrantHybridSearch(config)
        query_engine = qdrant_search.index.as_query_engine(**query_engine_kwargs)
        
    except Exception as e:
        print(e)
    # response=await pipeline.perform_query_async("How are you ?")
    

    
if __name__ == "__main__":
    asyncio.run(main())