import pytest
from llamasearch.pipeline import PipelineFactory
from llamasearch.settings import config

class BasePipelineTest:
    @pytest.fixture(autouse=True)
    async def setup_teardown(self):
        self.factory = PipelineFactory(config)
        await self.factory.initialize_common_resources()
        yield
        await self.factory.cleanup_all()

    async def run_query(self, pipeline, query: str):
        return await pipeline.perform_query_async(query)