import pytest
import configparser
import os
import subprocess
import json
from llama_index.core import SimpleDirectoryReader
from .api.generate_token import generate_firebase_tokens

# Test Constants
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

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    terminalreporter.write_sep("=", "Test summary")
    terminalreporter.write_line(f"Total tests: {terminalreporter.stats.get('total', 0)}")
    terminalreporter.write_line(f"Passed: {len(terminalreporter.stats.get('passed', []))}")
    terminalreporter.write_line(f"Failed: {len(terminalreporter.stats.get('failed', []))}")
    terminalreporter.write_line(f"Skipped: {len(terminalreporter.stats.get('skipped', []))}")

@pytest.fixture(scope="session")
def test_config():
    return {
        "base_dir": "data/test_docs/",
        "api_url": "http://localhost:8010/api/v1",
        "test_user_id": "test_user_123",
    }


@pytest.fixture(scope="module")
def ws_url():
    return WS_URL

@pytest.fixture(scope="module")
def api_url():
    return "http://localhost:8010/api/v1"

@pytest.fixture(scope="module")
def auth_token():
    return AUTH_TOKEN

@pytest.fixture(scope="module")
def invalid_token():
    return INVALID_TOKEN

@pytest.fixture(scope="module")
def test_files():
    return FILES

@pytest.fixture(scope="module")
def test_qa_dict():
    return QA_DICT

@pytest.fixture(scope="session")
def test_documents(test_config):
    return SimpleDirectoryReader(test_config["base_dir"], filename_as_id=True, required_exts=[".pdf"]).load_data()

@pytest.fixture(scope="session")
def qna_dataset():
    with open("tests/qna_dataset_20240911_103723.json", "r") as f:
        return json.load(f)

@pytest.fixture(scope="session")
def dvc_test_docs(test_config):
    # Ensure DVC data is pulled
    subprocess.run(["dvc", "pull", "data/test_docs.dvc"], check=True)
    return SimpleDirectoryReader(test_config["base_dir"], filename_as_id=True, required_exts=[".pdf"]).load_data()

@pytest.fixture(scope="session")
def upload_dir():
    upload_dir = "./test_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    yield upload_dir
    # Clean up after tests
    for file in os.listdir(upload_dir):
        os.remove(os.path.join(upload_dir, file))
    os.rmdir(upload_dir)
