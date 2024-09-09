import asyncio
import websockets
import json
import base64
import os
import pprint
import os
from dotenv import load_dotenv
from llamasearch.api.tests.generate_token import generate_firebase_tokens

load_dotenv()

def get_firebase_id_token():
    _, id_token = generate_firebase_tokens(os.getenv('FIREBASE_TEST_UID'), os.getenv('FIREBASE_CREDENTIALS_PATH'))
    return id_token

#--------------------------------------------------------------------------------
WS_URL = "ws://localhost:8010/ws"
AUTH_TOKEN = get_firebase_id_token()
INVALID_TOKEN = "invalid_token"
FILES = {
    "file1": "./data/test_docs/Adelaide_Strategic_Plan_2024_2028.pdf",
    "file2": "./data/test_docs/university-of-adelaide-enterprise-agreement-2023-2025_0.pdf",
    "file3": "./data/test_docs/meta-10k-1-5.pdf",
    "file4": "./data/test_docs/uber_10k-1-5.pdf"
}
#--------------------------------------------------------------------------------
qa_dict = {
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
#--------------------------------------------------------------------------------
async def authenticate(websocket, token):
    await websocket.send(json.dumps({
        "type": "auth",
        "token": f"Bearer {token}"
    }))
    response = await websocket.recv()
    return json.loads(response)


async def send_query(websocket, query, files=None, session_id=None):
    query_message = {
        "type": "query",
        "query": query,
        "stream": True,
        "files": [{'name': os.path.basename(f)} for f in files] if files else None,
        "session_id": session_id
    }
    if files:
        for file_path in files:
            with open(file_path, 'rb') as file:
                await websocket.send(file.read())
    await websocket.send(json.dumps(query_message))

async def receive_response(websocket):
    metadata = None
    full_response = ""
    while True:
        try:
            message = await asyncio.wait_for(websocket.recv(), timeout=30)
            data = json.loads(message)
            if data["type"] == "metadata":
                metadata = data
            elif data["type"] == "chunk":
                full_response += data['content']
            elif data["type"] == "end_stream":
                break
            elif data["type"] == "error":
                return data['content']
        except asyncio.TimeoutError:
            return "Timeout waiting for response"
    return {"metadata": metadata, "response": full_response}

async def test_query(query_id, files=None, token=AUTH_TOKEN):
    async with websockets.connect(WS_URL) as websocket:
        auth_response = await authenticate(websocket, token)
        assert auth_response['type'] == "authentication_success", f"Authentication failed: {auth_response}"
        session_id = auth_response['session_id']

        await send_query(websocket, qa_dict[query_id]['query'], files, session_id)
        response_data = await receive_response(websocket)
        # Parse the response JSON
        print(f"Response Data keys : {response_data.keys()}")
        response_expected_keys = ["response", "metadata"]
        for key in response_expected_keys:
            assert key in response_data, f"Expected key '{key}' not found in response"
        answer = response_data["response"]
        metadata = response_data["metadata"]
        # Check for expected keys in the response
        print(f"Metadata Keys : {metadata.keys()}")
        metadata_expected_keys = ["type", "context", "query", "file_upload"]
        for key in metadata_expected_keys:
            assert key in metadata, f"Expected key '{key}' not found in response"

        # Check if query matches the sent query
        assert metadata["query"] == qa_dict[query_id]['query'], "Query in response doesn't match sent query"

        if files:
            assert metadata["file_upload"], "File upload information is missing in response"
            uploaded_filenames = [file_info.get('filename') for file_info in metadata["file_upload"]]
            for file in files:
                assert os.path.basename(file) in uploaded_filenames, f"Expected file {os.path.basename(file)} not found in uploaded files"

        # Check if the type is 'metadata' as per the server response
        assert metadata["type"] == "metadata", "Expected response type to be 'metadata'"

        # Check if context is present and is a list
        assert isinstance(metadata["context"], list), "Expected context to be a list"

        return answer, metadata

#----------------------------------------

def pretty_print_result(scenario, response, metadata):
    print(f"\n--- Scenario {scenario} Results ---")
    print("Metadata:")
    pprint.pprint(metadata)
    print("\nAnswer:")
    print(response)
    print("--------")


async def test_scenario_1():
    """
    Scenario 1: Query without files, using websocket connection in stream mode.
    Tests the basic query functionality without file upload.
    """
    print("Testing scenario 1")
    response, metadata = await test_query(1)
    pretty_print_result(1, response, metadata)
    assert len(metadata["context"]) > 0, "Expected non-empty context"
    assert metadata["query"] == qa_dict[1]['query'], "Query mismatch"
    assert len(metadata["file_upload"]) == 0, "Expected empty file upload for this scenario"

async def test_scenario_2():
    """
    Scenario 2: Query with one file attached, using websocket connection in stream mode.
    Tests query processing with a single file upload.
    """
    print("Testing scenario 2")
    response, metadata = await test_query(2, [FILES['file1']])
    pretty_print_result(2, response, metadata)
    assert len(metadata["context"]) > 0, "Expected non-empty context"
    assert metadata["query"] == qa_dict[2]['query'], "Query mismatch"
    assert len(metadata["file_upload"]) == 1, "Expected one file upload for this scenario"
    assert metadata["file_upload"][0]["filename"] == os.path.basename(FILES['file1']), "Uploaded filename mismatch"

async def test_scenario_3():
    """
    Scenario 3: Query with two files attached, using websocket connection in stream mode.
    Tests query processing with multiple file uploads.
    """
    print("Testing scenario 3")
    response, metadata = await test_query(3, [FILES['file1'], FILES['file2']])
    pretty_print_result(3, response, metadata)
    assert len(metadata["context"]) > 0, "Expected non-empty context"
    assert metadata["query"] == qa_dict[3]['query'], "Query mismatch"
    assert len(metadata["file_upload"]) == 2, "Expected two file uploads for this scenario"
    uploaded_filenames = [file_info["filename"] for file_info in metadata["file_upload"]]
    assert os.path.basename(FILES['file1']) in uploaded_filenames, "First file not found in uploaded files"
    assert os.path.basename(FILES['file2']) in uploaded_filenames, "Second file not found in uploaded files"

async def test_scenario_4():
    """
    Scenario 4: Another query with two files attached, using websocket connection in stream mode.
    Verifies consistent behavior with multiple file uploads and different query.
    """
    print("Testing scenario 4")
    response, metadata = await test_query(4, [FILES['file1'], FILES['file2']])
    pretty_print_result(4, response, metadata)
    assert len(metadata["context"]) > 0, "Expected non-empty context"
    assert metadata["query"] == qa_dict[4]['query'], "Query mismatch"
    assert len(metadata["file_upload"]) == 2, "Expected two file uploads for this scenario"
    uploaded_filenames = [file_info["filename"] for file_info in metadata["file_upload"]]
    assert os.path.basename(FILES['file1']) in uploaded_filenames, "First file not found in uploaded files"
    assert os.path.basename(FILES['file2']) in uploaded_filenames, "Second file not found in uploaded files"


async def test_scenario_5():
    """
    Scenario 5: Repeat of Scenario 1 - Query without files, using websocket connection in stream mode.
    Ensures consistent behavior when querying without files after previous file uploads.
    """
    print("Testing scenario 5")
    response, metadata = await test_query(1)
    pretty_print_result(5, response, metadata)
    assert len(metadata["context"]) > 0, "Expected non-empty context"
    assert metadata["query"] == qa_dict[1]['query'], "Query mismatch"
    assert len(metadata["file_upload"]) == 0, "Expected empty file upload for this scenario"

async def test_scenario_6():
    """
    Scenario 6: Query with file attached, using websocket connection with invalid token in stream mode.
    Tests the system's response to authentication failure.
    """
    print("Testing scenario 6")
    try:
        async with websockets.connect(WS_URL) as websocket:
            await authenticate(websocket, INVALID_TOKEN)
        assert False, "Expected authentication failure, but request succeeded"
    except websockets.exceptions.ConnectionClosedError as e:
        assert e.code == 1011, f"Expected close code 1011, got {e.code}"
        print(f"Authentication failed as expected: {e}")
    except AssertionError as e:
        assert "Authentication failed" in str(e), "Expected authentication failure for invalid token"

if __name__ == "__main__":
    asyncio.run(test_scenario_1())
    asyncio.run(test_scenario_2())
    asyncio.run(test_scenario_3())
    asyncio.run(test_scenario_4())
    asyncio.run(test_scenario_5())
    asyncio.run(test_scenario_6())
