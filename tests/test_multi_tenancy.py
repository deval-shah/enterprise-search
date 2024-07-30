import pytest
import asyncio
from llamasearch.pipeline import PipelineFactory
from llamasearch.settings import config
import os
from typing import List, Dict
import configparser
import os

test_config = configparser.ConfigParser()
test_config.read(os.path.join(os.path.dirname(__file__), 'test_config.ini'))

base_dir = test_config['paths']['base_dir']

class TestResultPrinter:
    @staticmethod
    def print_test_result(test_name: str, response, pipeline):
        print(f"\n{'=' * 80}")
        print(f"Test: {test_name}")
        print(f"{'-' * 80}")
        print(f"Response: {response}")
        print(f"{'-' * 80}")
        pipeline.pretty_print_context(response)
        print(f"{'=' * 80}\n")

class BaseTest:
    @pytest.fixture(autouse=True)
    async def setup_teardown(self):
        self.factory = PipelineFactory()
        yield
        await self.factory.cleanup_all()

    async def run_query(self, pipeline, query: str, test_name: str):
        response = await pipeline.perform_query_async(query)
        TestResultPrinter.print_test_result(test_name, response, pipeline)
        return response

class TestMultiTenancy(BaseTest):
    @pytest.fixture(autouse=True)
    def set_multi_tenancy(self):
        config.vector_store_config.multi_tenancy = True

    def assert_tenant_id(self, response, expected_tenant_id: str):
        for node in response.source_nodes:
            print("Tenant ID : {} Expected : {}".format(node.metadata.get('tenant_id'), expected_tenant_id))
        assert all(node.metadata.get('tenant_id') == expected_tenant_id for node in response.source_nodes)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("scenario", [
        {
            "name": "test_multi_tenant_scenario",
            "tenants": [
                {"user": "user1", "tenant": "tenant1", "docs": ["Llama_Paper.pdf", "meta-10k-1-5.pdf"]},
                {"user": "user2", "tenant": "tenant2", "docs": ["uber_10k-1-5.pdf", "meta-10k-1-5.pdf"]}
            ],
            "queries": ["What are key contributins of LLaMA paper?", # Only user1 should be able to answer this query
                        "Summarise family metrics of Meta?"] # Both users should be able to answer this query
        },
        {
            "name": "test_data_isolation",
            "tenants": [
                {"user": "user3", "tenant": "tenant3", "docs": ["Llama_Paper.pdf"]},
                {"user": "user4", "tenant": "tenant4", "docs": ["meta-10k-1-5.pdf"]}
            ],
            "queries": ["Summarise family metrics of Meta?", # Only user4 should be able to answer this query
                        "List different categories of LLama models"] # Only user3 should be able to answer this query
        }
    ])
    async def test_multi_tenancy(self, scenario: Dict):
        pipelines = {}
        # Setup pipelines and insert documents
        for tenant in scenario["tenants"]:
            pipeline = await self.factory.get_or_create_pipeline_async(tenant["user"], tenant["tenant"])
            pipelines[tenant["user"]] = pipeline
            await pipeline.insert_documents([os.path.join(base_dir, doc) for doc in tenant["docs"]])
        # Run queries and assert results
        for query in scenario["queries"]:
            for tenant in scenario["tenants"]:
                response = await self.run_query(pipelines[tenant["user"]], query, f"{scenario['name']} - {tenant['user']} - {tenant['tenant']}")
                self.assert_tenant_id(response, tenant["tenant"])

        print(f"{scenario['name']} passed")

class TestSingleTenant(BaseTest):
    @pytest.fixture(autouse=True)
    def set_single_tenancy(self):
        config.vector_store_config.multi_tenancy = False

    @pytest.mark.asyncio
    @pytest.mark.parametrize("scenario", [
        {
            "name": "test_single_tenant_scenario",
            "user": "user1",
            "docs": ["uber_10k-1-5.pdf", "meta-10k-1-5.pdf"],
            "queries": ["List different categories of LLama models"] # Should get an answer from global index
        },
        {
            "name": "test_global_search",
            "user": "user2",
            "docs": ["Llama_Paper.pdf", "meta-10k-1-5.pdf"],
            "queries": ["List different categories of LLama models"] # Should get an answer
        }
    ])
    async def test_single_tenancy(self, scenario: Dict):
        # Setup pipeline and insert documents
        pipeline = await self.factory.create_pipeline_async(scenario["user"], None)
        await pipeline.insert_documents([os.path.join(base_dir, doc) for doc in scenario["docs"]])
        # Run queries and assert results
        for query in scenario["queries"]:
            response = await self.run_query(pipeline, query, f"{scenario['name']} - {scenario['user']}")
            assert response is not None
            assert len(response.source_nodes) > 0
        print(f"{scenario['name']} passed")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
