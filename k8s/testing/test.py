import requests
import pytest
import os

class TestAPISuite:
    """Integration tests for API endpoints."""

    @pytest.fixture(scope='class')
    def base_url(self):
        """Base URL for the API."""
        return "http://127.0.0.1:8000"

    @pytest.mark.parametrize("query,expected_status", [
        ('What is BCG?', 200),
        ('', 422),  # Assuming an empty query might lead to a bad request status.
    ])
    def test_query_endpoint(self, base_url, query, expected_status):
        """Test the /query/ endpoint with various POST requests."""
        response = requests.post(f"{base_url}/query/", data={"query": query})
        assert response.status_code == expected_status
        if response.status_code == 200:
            assert 'response' in response.json()

    @pytest.mark.parametrize("file_name, content_type, expected_status", [
        ('data/test.pdf', 'application/pdf', 200)
    ])
    def test_upload_files(self, base_url, file_name, content_type, expected_status):
        """Test the file upload functionality with different file types."""
        with open(file_name, 'rb') as file:
            files = {'files': (os.path.basename(file_name), file, content_type)}
            response = requests.post(f"{base_url}/uploadfile/", files=files)
            if response.status_code != expected_status:
                print("Failed to upload file:", response.text)  # Log the error message from the API
            assert response.status_code == expected_status

    @pytest.mark.parametrize("file_name, query, expected_status", [
        ('data/test.pdf', 'What is BCG?', 200),
        ('data/empty.txt', 'What is BCG?', 200),
        ('data/test.pdf', '', 422)  # Assuming an empty query results in a bad request.
    ])
    def test_query_with_files(self, base_url, file_name, query, expected_status):
        """Test the /query/ endpoint with file upload and different queries."""
        with open(file_name, 'rb') as file:
            files = {'file': (os.path.basename(file_name), file, 'text/plain')}
            data = {'query': query}
            response = requests.post(f"{base_url}/query/", files=files, data=data)
            assert response.status_code == expected_status
            if response.status_code == 200:
                assert 'file_upload' in response.json()