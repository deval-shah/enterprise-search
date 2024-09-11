import asyncio
import pytest
import websockets
import json
import base64
import os
from dotenv import load_dotenv
from llamasearch.api.tests.generate_token import generate_firebase_tokens
from llamasearch.api.websocket_manager import ConnectionManager
from llamasearch.api.query_processor import process_query

load_dotenv()

#----------------------------------------------------------------------------------------------------------------------------------
WS_URL = "ws://localhost:8010/ws"
AUTH_TOKEN = generate_firebase_tokens(os.getenv('FIREBASE_TEST_UID'), os.getenv('FIREBASE_CREDENTIALS_PATH'))[1]
INVALID_TOKEN = "invalid_token"
FILES = {
    "file1": "./data/test_docs/Adelaide_Strategic_Plan_2024_2028.pdf",
    "file2": "./data/test_docs/university-of-adelaide-enterprise-agreement-2023-2025_0.pdf",
    "file3": "./data/test_docs/meta-10k-1-5.pdf",
    "file4": "./data/test_docs/uber_10k-1-5.pdf"
}
QA_DICT = {
    1: {
        "query": "What is the vision for Adelaide's economy in 10 years according to the strategic plan?",
        "filename": "Adelaide_Strategic_Plan_2024_2028.pdf",
        "expected_answer": "In 10 years, Adelaide will be the strong economic focal point of the state, attracting investment and talent from around the world. New and diverse industries will complement and build on existing economic strengths, and city businesses will be successful and connected to global opportunities."
    },
    2: {
        "query": "What are the progressive Indigenous employment targets set out in the strategic plan?",
        "filename": "Adelaide_Strategic_Plan_2024_2028.pdf",
        "expected_answer": "The strategic plan sets out the following progressive Indigenous employment targets: 75 Indigenous staff members by 2023, 80 Indigenous staff members by 2024, and 85 Indigenous staff members by 2025."
    },
    3: {
        "query": "What salary increases are included in the 2023-2025 Enterprise Agreement?",
        "filename": "university-of-adelaide-enterprise-agreement-2023-2025_0.pdf",
        "expected_answer": "The Enterprise Agreement includes the following salary increases: a 4.2% increase applied from 1 July 2023, a 3.5% increase applied from 29 June 2024, and a 3.5% increase applied from 28 June 2025."
    },
    4: {
        "query": "What is the employer superannuation contribution for staff employed on a continuing or fixed-term basis?",
        "filename": "university-of-adelaide-enterprise-agreement-2023-2025_0.pdf",
        "expected_answer": "The University will make employer superannuation contributions of 17% for staff employed on a continuing or fixed-term basis."
    },
    5: {
        "query": "What Family metrics will Meta continue to report in its periodic reports filed with the SEC?",
        "filename": "meta-10k-1-5.pdf",
        "expected_answer": "Beginning with the Quarterly Report on Form 10-Q for the first quarter of 2024, Meta will continue reporting DAP (daily active people) and ARPP (average revenue per person) in its periodic reports filed with the Securities and Exchange Commission."
    },
    6: {
        "query": "What is the estimated error margin for Meta's Family metrics?",
        "filename": "meta-10k-1-5.pdf",
        "expected_answer": "Meta estimates that the error margin for their Family metrics generally will be approximately 3% of their worldwide MAP (monthly active people)."
    },
    7: {
        "query": "What are some of the key forward-looking statements mentioned in Uber's Annual Report?",
        "filename": "uber_10k-1-5.pdf",
        "expected_answer": "Some key forward-looking statements mentioned include Uber's expectations regarding financial performance, future operating performance, investments in new products and offerings, ability to close and integrate acquisitions, anticipated technology trends, growth in the number of platform users, ability to introduce new products and enhance existing ones, and ability to expand internationally."
    },
    8: {
        "query": "How often does Uber undertake to update its forward-looking statements?",
        "filename": "uber_10k-1-5.pdf",
        "expected_answer": "Uber states that they undertake no obligation to update any forward-looking statements made in the Annual Report to reflect events or circumstances after the date of the report or to reflect new information, actual results, revised expectations, or the occurrence of unanticipated events, except as required by law."
    }
}
#----------------------------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def event_loop():
    """Provide an event loop for asyncio tests."""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def websocket():
    """Yield a connected websocket for each test."""
    async with websockets.connect(WS_URL) as ws:
        yield ws

@pytest.fixture
async def authenticated_websocket(websocket):
    """Yield an authenticated websocket connection."""
    await authenticate(websocket, AUTH_TOKEN)
    return websocket

async def authenticate(websocket, token):
    """Helper function to authenticate a websocket connection."""
    await websocket.send(json.dumps({"type": "auth", "token": f"Bearer {token}"}))
    try:
        return await websocket.recv()
    except websockets.exceptions.ConnectionClosedError:
        return None

@pytest.mark.asyncio
async def test_authentication_success(websocket):
    """Test successful authentication with a valid token."""
    response = await authenticate(websocket, AUTH_TOKEN)
    assert json.loads(response)['type'] == "authentication_success"

@pytest.mark.asyncio
async def test_authentication_failure_query(websocket):
    """Test query with authentication failure."""
    response = await authenticate(websocket, INVALID_TOKEN)
    assert response is None
    with pytest.raises(websockets.exceptions.ConnectionClosedError):
        await send_and_receive_query(websocket, QA_DICT[1]['query'])

@pytest.mark.asyncio
@pytest.mark.parametrize("query_id", [1, 2, 3, 4])
async def test_query_without_files(authenticated_websocket, query_id):
    """Test querying without file attachments."""
    response = await send_and_receive_query(authenticated_websocket, QA_DICT[query_id]['query'])
    assert_valid_response(response, query_id)

@pytest.mark.asyncio
@pytest.mark.parametrize("query_id,file_keys", [(2, ['file1']), (3, ['file1', 'file2'])])
async def test_query_with_files(authenticated_websocket, query_id, file_keys):
    """Test querying with file attachments."""
    files = [FILES[key] for key in file_keys]
    response = await send_and_receive_query(authenticated_websocket, QA_DICT[query_id]['query'], files)
    assert_valid_response(response, query_id)
    assert len(response['metadata']['file_upload']) == len(files)

@pytest.mark.asyncio
async def test_query_with_invalid_file_data(authenticated_websocket):
    """Test querying with invalid file data."""
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
    assert response_data['content'] == "Invalid file data"
    assert "nonexistent.pdf" in response_data['invalid_files']

@pytest.mark.asyncio
@pytest.mark.parametrize("query_id,file_keys", [(5, ['file3']), (6, ['file3']), (7, ['file4']), (8, ['file4'])])
async def test_query_with_multiple_files(authenticated_websocket, query_id, file_keys):
    """Test querying with multiple file attachments."""
    files = [FILES[key] for key in file_keys]
    response = await send_and_receive_query(authenticated_websocket, QA_DICT[query_id]['query'], files)
    assert_valid_response(response, query_id)
    assert len(response['metadata']['file_upload']) == len(files)

@pytest.mark.asyncio
async def test_query_consistency(authenticated_websocket):
    """Test consistency of behavior across different queries."""
    for query_id in [1, 3, 5, 7]:
        response = await send_and_receive_query(authenticated_websocket, QA_DICT[query_id]['query'])
        assert_valid_response(response, query_id)

@pytest.mark.asyncio
async def test_query_statelessness(authenticated_websocket):
    """Test statelessness of the query system."""
    # First query with file upload
    response1 = await send_and_receive_query(authenticated_websocket, QA_DICT[2]['query'], [FILES['file1']])
    assert_valid_response(response1, 2)
    
    # Second query without file upload
    response2 = await send_and_receive_query(authenticated_websocket, QA_DICT[1]['query'])
    assert_valid_response(response2, 1)
    assert len(response2['metadata']['file_upload']) == 0

@pytest.mark.asyncio
async def test_authentication_failure_query(websocket):
    """Test query with authentication failure."""
    await authenticate(websocket, INVALID_TOKEN)
    with pytest.raises(websockets.exceptions.ConnectionClosedError):
        await send_and_receive_query(websocket, QA_DICT[1]['query'])

async def send_and_receive_query(websocket, query, files=None):
    """Helper function to send a query and receive the response."""
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
                query_message["files"].append({
                    "name": os.path.basename(file_path),
                    "error": "File not found"
                })
                return {"response": "File not found", "metadata": {}}
    
    await websocket.send(json.dumps(query_message))
    return await receive_response(websocket)

async def receive_response(websocket):
    """Helper function to receive and compile the full response."""
    metadata = None
    full_response = ""
    while True:
        message = await websocket.recv()
        data = json.loads(message)
        if data["type"] == "metadata":
            metadata = data
        elif data["type"] == "chunk":
            full_response += data['content']
        elif data["type"] == "end_stream":
            break
        elif data["type"] == "error":
            return {"response": data['content'], "metadata": metadata}
    return {"response": full_response, "metadata": metadata}

def assert_valid_response(response, query_id):
    """Helper function to assert the validity of a response."""
    assert "response" in response
    assert "metadata" in response
    assert response['metadata']['query'] == QA_DICT[query_id]['query']
    assert isinstance(response['metadata']['context'], list)
    assert response['metadata']['type'] == "metadata"

if __name__ == "__main__":
    pytest.main([__file__])
