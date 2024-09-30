import pytest
import requests
import json
import os
from .base_api_test import BaseAPITest
from llamasearch.api.core.config import settings
from io import BytesIO

class TestHTTPAPI(BaseAPITest):
    @pytest.fixture(autouse=True)
    def setup_test_data(self, test_qa_dict):
        self.test_qa_dict = test_qa_dict

    @pytest.mark.parametrize("query_id", [1, 2, 3, 4])
    def test_query_endpoint(self, api_url, auth_token, test_files, query_id):
        query = self.test_qa_dict[query_id]['query']
        file_key = f"file{query_id}"
        file_path = test_files.get(file_key)

        files = None
        if file_path:
            files = [('files', (os.path.basename(file_path), open(file_path, 'rb'), 'application/pdf'))]

        try:
            response = requests.post(
                f"{api_url}/query/",
                headers={"Authorization": f"Bearer {auth_token}"},
                data={"query": query},
                files=files
            )

            assert response.status_code == 200
            response_data = response.json()
            self.assert_valid_response(response_data, query_id)
        except Exception as e:
            print(f"Error occurred during test: {e}")
            raise

    def test_query_without_auth(self, api_url):
        response = requests.post(f"{api_url}/query/", data={"query": "Test query"})
        assert response.status_code == 401

    def test_query_with_invalid_auth(self, api_url, invalid_token):
        response = requests.post(
            f"{api_url}/query/",
            headers={"Authorization": f"Bearer {invalid_token}"},
            data={"query": "Test query"}
        )
        assert response.status_code == 401

    def test_query_with_empty_query(self, api_url, auth_token):
        response = requests.post(
            f"{api_url}/query/",
            headers={"Authorization": f"Bearer {auth_token}"},
            data={"query": ""}
        )
        assert response.status_code == 422

    def test_query_with_empty_string(self, api_url, auth_token):
        response = requests.post(
            f"{api_url}/query/",
            headers={"Authorization": f"Bearer {auth_token}"},
            data={"query": ""}
        )
        assert response.status_code == 422
        assert "Empty query string is not allowed" in response.json()['detail']

    def test_upload_file_success(self, api_url, auth_token, test_files):
        file_path = test_files['file1']
        with open(file_path, 'rb') as f:
            files = {'files': (os.path.basename(file_path), f, 'application/pdf')}
            response = requests.post(
                f"{api_url}/uploadfile",
                headers={"Authorization": f"Bearer {auth_token}"},
                files=files
            )
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.content}")
        assert response.status_code == 200
        assert 'file_upload' in response.json()

    def test_upload_file_no_file(self, api_url, auth_token):
        response = requests.post(
            f"{api_url}/uploadfile",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 422

    def test_upload_file_invalid_type(self, api_url, auth_token):
        files = {'files': ('test.csv', BytesIO(b'Invalid file type'), 'text/plain')}
        response = requests.post(
            f"{api_url}/uploadfile",
            headers={"Authorization": f"Bearer {auth_token}"},
            files=files
        )
        assert response.status_code == 400

    def test_insert_documents(self, api_url, auth_token, test_files):
        file_path = test_files['file1']
        with open(file_path, 'rb') as f:
            files = {'files': (os.path.basename(file_path), f, 'application/pdf')}
            response = requests.post(
                f"{api_url}/documents/insert",
                headers={"Authorization": f"Bearer {auth_token}"},
                files=files
            )

        assert response.status_code == 200
        response_data = response.json()
        assert response_data['status'] == 'success'
        assert 'data' in response_data
        assert len(response_data['data']) == 1
        assert response_data['data'][0]['filename'] == os.path.basename(file_path)
        assert response_data['data'][0]['status'] == 'inserted'

    def test_delete_documents(self, api_url, auth_token, test_files):
        # First, insert a document
        file_path = test_files['file1']
        with open(file_path, 'rb') as f:
            files = {'files': (os.path.basename(file_path), f, 'application/pdf')}
            insert_response = requests.post(
                f"{api_url}/documents/insert",
                headers={"Authorization": f"Bearer {auth_token}"},
                files=files
            )
        assert insert_response.status_code == 200

        # Now, delete the document
        filename = os.path.basename(file_path)
        delete_response = requests.delete(
            f"{api_url}/documents/delete",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            json={"filenames": [filename]}
        )

        assert delete_response.status_code == 200
        delete_data = delete_response.json()
        assert 'results' in delete_data
        assert delete_data['results'][filename] == "Deleted successfully"

    def assert_valid_response(self, response, query_id):
        assert "response" in response
        assert "context" in response
        assert response['query'] == self.test_qa_dict[query_id]['query']
        assert isinstance(response['context'], list)

        if 'file_upload' in response:
            assert isinstance(response['file_upload'], list)

if __name__ == "__main__":
    pytest.main([__file__])
