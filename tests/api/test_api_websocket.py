import asyncio
import pytest
import websockets
import json
import base64
import os
from .base_api_test import BaseAPITest

class TestWebSocketAPI(BaseAPITest):
    @pytest.fixture(autouse=True)
    def setup_test_data(self, test_qa_dict):
        self.test_qa_dict = test_qa_dict

    @pytest.fixture(scope="module")
    def event_loop(self):
        loop = asyncio.get_event_loop()
        yield loop
        loop.close()

    @pytest.fixture
    async def websocket(self, ws_url):
        async with websockets.connect(ws_url) as ws:
            yield ws

    @pytest.fixture
    async def authenticated_websocket(self, websocket, auth_token):
        await self.authenticate(websocket, auth_token)
        return websocket

    async def authenticate(self, websocket, token):
        await websocket.send(json.dumps({"type": "auth", "token": f"Bearer {token}"}))
        try:
            return await websocket.recv()
        except websockets.exceptions.ConnectionClosedError:
            return None

    @pytest.mark.asyncio
    async def test_authentication_success(self, websocket, auth_token):
        response = await self.authenticate(websocket, auth_token)
        assert json.loads(response)['type'] == "authentication_success"

    @pytest.mark.asyncio
    async def test_authentication_failure_query(self, websocket, invalid_token):
        response = await self.authenticate(websocket, invalid_token)
        assert response is None
        with pytest.raises(websockets.exceptions.ConnectionClosedError):
            await self.send_and_receive_query(websocket, self.test_qa_dict[1]['query'])

    @pytest.mark.asyncio
    @pytest.mark.parametrize("query_id", [1, 2, 3, 4])
    async def test_query_without_files(self, authenticated_websocket, query_id):
        response = await self.send_and_receive_query(authenticated_websocket, self.test_qa_dict[query_id]['query'])
        self.assert_valid_response(response, query_id)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("query_id,file_keys", [(2, ['file1']), (3, ['file1', 'file2'])])
    async def test_query_with_files(self, authenticated_websocket, query_id, file_keys, test_files):
        files = [test_files[key] for key in file_keys]
        response = await self.send_and_receive_query(authenticated_websocket, self.test_qa_dict[query_id]['query'], files)
        self.assert_valid_response(response, query_id)

        if 'file_upload' in response['metadata']:
            assert len(response['metadata']['file_upload']) == len(files)
        else:
            print(f"Warning: 'file_upload' key not found in response metadata for query_id {query_id}")
            print(f"Response metadata: {response['metadata']}")

    @pytest.mark.asyncio
    async def test_query_with_invalid_file_data(self, authenticated_websocket):
        query_message = {
            "type": "query",
            "query": "Test query",
            "stream": True,
            "files": [{
                "name": "nonexistent.pdf",
                "content": ""  # Empty content to simulate missing file
            }],
            "session_id": "test_session"
        }

        await authenticated_websocket.send(json.dumps(query_message))
        response = await authenticated_websocket.recv()
        response_data = json.loads(response)

        assert response_data['type'] == "error"
        assert "Invalid file data" in response_data['content']['error']
        assert "nonexistent.pdf" in response_data['content']['invalid_files']

    @pytest.mark.asyncio
    @pytest.mark.parametrize("query_id,file_keys", [(5, ['file3']), (6, ['file3']), (7, ['file4']), (8, ['file4'])])
    async def test_query_with_multiple_files(self, authenticated_websocket, query_id, file_keys, test_files):
        files = [test_files[key] for key in file_keys]
        response = await self.send_and_receive_query(authenticated_websocket, self.test_qa_dict[query_id]['query'], files)
        self.assert_valid_response(response, query_id)
        assert len(response['metadata']['file_upload']) == len(files)

    @pytest.mark.asyncio
    async def test_query_consistency(self, authenticated_websocket):
        for query_id in [1, 3, 5, 7]:
            response = await self.send_and_receive_query(authenticated_websocket, self.test_qa_dict[query_id]['query'])
            self.assert_valid_response(response, query_id)

    @pytest.mark.asyncio
    async def test_query_statelessness(self, authenticated_websocket, test_files):
        response1 = await self.send_and_receive_query(authenticated_websocket, self.test_qa_dict[2]['query'], [test_files['file1']])
        self.assert_valid_response(response1, 2)

        response2 = await self.send_and_receive_query(authenticated_websocket, self.test_qa_dict[1]['query'])
        self.assert_valid_response(response2, 1)
        assert len(response2['metadata']['file_upload']) == 0

    async def send_and_receive_query(self, websocket, query, files=None):
        query_message = {
            "type": "query",
            "query": query,
            "stream": True,
            "files": [],
            "session_id": "test_session"
        }
        if files:
            for file_path in files:
                try:
                    with open(file_path, 'rb') as file:
                        file_content = file.read()
                        query_message["files"].append({
                            "name": os.path.basename(file_path),
                            "content": base64.b64encode(file_content).decode('utf-8')
                        })
                except FileNotFoundError:
                    return {"response": "File not found", "metadata": {}}

        await websocket.send(json.dumps(query_message))
        return await self.receive_response(websocket)

    async def receive_response(self, websocket):
        metadata = None
        full_response = ""
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            if data["type"] == "metadata":
                metadata = data["content"]
            elif data["type"] == "chunk":
                full_response += data['content'] + " "
            elif data["type"] == "end_stream":
                break
            elif data["type"] == "error":
                return {"response": data['content']['error'], "metadata": metadata}
        return {"response": full_response.strip(), "metadata": metadata}

    def assert_valid_response(self, response, query_id):
        assert "response" in response
        assert "metadata" in response
        assert isinstance(response['metadata'], dict)

        if response['response'] == 'File not found':
            # For file not found cases, we don't expect query in metadata
            assert 'file_upload' not in response['metadata']
        else:
            # For successful queries
            assert 'query' in response['metadata'], f"Expected 'query' in metadata, got: {response['metadata']}"
            assert response['metadata']['query'] == self.test_qa_dict[query_id]['query']
            assert 'context' in response['metadata']
            assert isinstance(response['metadata']['context'], list)

        if 'file_upload' in response['metadata']:
            assert isinstance(response['metadata']['file_upload'], list)

if __name__ == "__main__":
    pytest.main([__file__])