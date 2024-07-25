import asyncio
from llamasearch.pipeline import PipelineFactory
from llamasearch.settings import config
import os

ENABLE_MULTI_TENANCY = True  # Toggle this to switch between multi-tenant and single-tenant modes

base_dir  = "data/sample-docs/slim/"
filenames = ['Llama_Paper.pdf', 'meta-10k-1-5.pdf', 'uber_10k-1-5.pdf',\
    'Reduce_Hallucinations_RAG_Paper.pdf', 'Resume.pdf', 'Singapore_Krisflyer_Points.pdf']

test_config = {
    "multi_tenant": [
        {
            "name": "test_multi_tenant_scenario",
            "tenants": [
                {"user": "user1", "tenant": "tenant1", "docs": ["Llama_Paper.pdf", "meta-10k-1-5.pdf"]},
                {"user": "user2", "tenant": "tenant2", "docs": ["uber_10k-1-5.pdf", "Reduce_Hallucinations_RAG_Paper.pdf"]}
            ],
            "queries": ["LLaMA-65B is competitive with which models?"]
        },
        {
            "name": "test_data_isolation",
            "tenants": [
                {"user": "user3", "tenant": "tenant3", "docs": ["Llama_Paper.pdf"]},
                {"user": "user4", "tenant": "tenant4", "docs": ["meta-10k-1-5.pdf"]}
            ],
            "queries": ["LLaMA-65B is competitive with which models?", "Summarise family metrics of Meta?"]
        }
    ],
    "single_tenant": [
        {
            "name": "test_single_tenant_scenario",
            "docs": ["Llama_Paper.pdf", "meta-10k-1-5.pdf"],
            "queries": ["What is RAG?"]
        },
        {
            "name": "test_global_search",
            "docs": ["Llama_Paper.pdf", "meta-10k-1-5.pdf"],
            "queries": ["Why did uber acquire Drizly?"]
        }
    ]
}

#---------------------------
# Multi Tentant Test Cases |
#---------------------------
async def test_multi_tenant_scenario(factory):
    print("\n---------------------------TEST MULTI TENANT SCENARIO-------------------------------\n")
    pipeline1 = await factory.get_or_create_pipeline_async("user1", "tenant1")
    pipeline2 = await factory.get_or_create_pipeline_async("user2", "tenant2")

    await pipeline1.insert_documents([ os.path.join(base_dir,filenames[0]), os.path.join(base_dir,filenames[1]) ] )
    await pipeline2.insert_documents([ os.path.join(base_dir,filenames[2]), os.path.join(base_dir,filenames[3]) ])

    query1 = "LLaMA-65B is competitive with which models?" # Should be answered from user1 docs
    query2 = "Summarise family metrics of Meta?" # Should be answered from user1 docs
    query3 = "List some important forward-looking statements of Uber?" # Should be answered from user2 docs
    response1 = await pipeline1.perform_query_async(query1)
    response2 = await pipeline2.perform_query_async(query1)
    
    print(f"Tenant 1 results :: Response: {response1}")
    pipeline1.pretty_print_context(response1)
    for node in response1.source_nodes:
        print(node.metadata)
    
    print("\n")
    
    print(f"Tenant 2 results :: Response: {response2}")
    pipeline2.pretty_print_context(response2)
    for node in response2.source_nodes:
        print(node.metadata)
    
    print("------------------------------------------------------------------------------------\n")

    assert all(node.metadata.get('tenant_id') == "tenant1" for node in response1.source_nodes)
    assert all(node.metadata.get('tenant_id') == "tenant2" for node in response2.source_nodes)

async def test_data_isolation(factory):
    print("\n---------------------------TEST DATA ISOLATION SCENARIO-------------------------------\n")
    pipeline3 = await factory.get_or_create_pipeline_async("user3", "tenant3")
    pipeline4 = await factory.get_or_create_pipeline_async("user4", "tenant4")
    
    await pipeline3.insert_documents([base_dir+filenames[0]]) # LLama paper
    await pipeline4.insert_documents([base_dir+filenames[1]]) # Meta

    query1 = "LLaMA-65B is competitive with which models?" # Should be answered from user1 docs
    query2 = "Summarise family metrics of Meta?" # Should be answered from user1 docs
    response1 = await pipeline3.perform_query_async(query1)
    response2 = await pipeline4.perform_query_async(query2)

    print(f"Tenant 1 results :: Response: {response1}")
    pipeline3.pretty_print_context(response1)
    for node in response1.source_nodes:
        print(node.metadata)

    print("\n")
    print(f"Tenant 2 results :: Response: {response2}")
    pipeline4.pretty_print_context(response2)
    for node in response2.source_nodes:
        print(node.metadata)

    assert all(node.metadata.get('tenant_id') == "tenant3" for node in response1.source_nodes)
    assert all(node.metadata.get('tenant_id') == "tenant4" for node in response2.source_nodes)

    print("Data isolation test passed")
    print("------------------------------------------------------------------------------------\n")

#----------------------------
# Single Tentant Test Cases |
#----------------------------
async def test_single_tenant_scenario(factory):
    print("\n---------------------------TEST SINGLE TENANT SCENARIO-------------------------------\n")
    factory = PipelineFactory()
    pipeline = await factory.create_pipeline_async("user1", None)
    
    await pipeline.insert_documents([base_dir+filenames[0], base_dir+filenames[1]])
    query = "What is RAG?" # could be answered from both docs
    response = await pipeline.perform_query_async(query)
    
    print(f"Single tenant results :: Response: {response}")
    pipeline.pretty_print_context(response)
    print("------------------------------------------------------------------------------------\n")

    assert response is not None
    assert len(response.source_nodes) > 0

async def test_global_search(factory):
    print("\n---------------------------TEST GLOBAL SEARCH SCENARIO-------------------------------\n")
    pipeline = await factory.create_pipeline_async("user1", None)
    
    await pipeline.insert_documents([base_dir+filenames[0], base_dir+filenames[1]])
    
    query = "Why did uber acquired Drizly?" # The docs does not contain answer to this query
    response = await pipeline.perform_query_async(query)

    print(f"Single tenant results :: Response: {response}")
    pipeline.pretty_print_context(response)

    for node in response.source_nodes:
        print(node.metadata)
    assert len(response.source_nodes) == 2
    print("Global search test passed")
    print("------------------------------------------------------------------------------------\n")

async def run_tests():
    config.vector_store_config.multi_tenancy = ENABLE_MULTI_TENANCY
    factory = PipelineFactory()
    try:
        if ENABLE_MULTI_TENANCY:
            print("Running multi-tenant tests...")
            await test_multi_tenant_scenario(factory)
            await test_data_isolation(factory)
        else:
            print("Running single-tenant tests...")
            await test_single_tenant_scenario(factory)
            await test_global_search()
    finally:
        await factory.cleanup_all()
        print("All tests completed and resources cleaned up")

if __name__ == "__main__":
    asyncio.run(run_tests())