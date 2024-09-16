import pytest
from fastapi.testclient import TestClient
from llamasearch.api.main import app
from llamasearch.api.db.session import init_db, close_db

class BaseAPITest:
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        self.client = TestClient(app)
        yield
        # Add any API-specific teardown if needed

    #@pytest.fixture(autouse=True)
    #async def setup_db(self):
    #    # Initialize the database connection
    #    await init_db()
    #    yield
    #    await close_db()

    async def send_query(self, query: str, files=None):
        # Implement a method to send queries to the API
        pass
