import pytest
import configparser
import os
import subprocess
import json
from llama_index.core import SimpleDirectoryReader
from .api.generate_token import generate_firebase_tokens

# Test Constants
WS_URL = "ws://localhost:8010/ws"
AUTH_TOKEN = generate_firebase_tokens()[1]
INVALID_TOKEN = "invalid_token"

# Test Configuration
FILES = {
    "file1": "./data/test_docs/attention_is_all_you_need.pdf",
    "file2": "./data/test_docs/meta_10k.pdf",
    "file3": "./data/test_docs/adelaide_strategic_plan_2024_2028.pdf",
    "file4": "./data/test_docs/paul_graham_essay.txt"
}

QA_DICT = {
    1: {
        "query": "What is the main innovation introduced in the paper 'Attention Is All You Need'?",
        "filename": "attention_is_all_you_need.pdf",
        "expected_answer": "The main innovation is the Transformer, a new simple network architecture based solely on attention mechanisms, dispensing with recurrence and convolutions entirely."
    },
    2: {
        "query": "How many NVIDIA P100 GPUs were used to train the base Transformer model?",
        "filename": "attention_is_all_you_need.pdf",
        "expected_answer": "The base Transformer model was trained on 8 NVIDIA P100 GPUs."
    },
    3: {
        "query": "What BLEU score did the big Transformer model achieve on the WMT 2014 English-to-German translation task?",
        "filename": "attention_is_all_you_need.pdf",
        "expected_answer": "The big Transformer model achieved a BLEU score of 28.4 on the WMT 2014 English-to-German translation task."
    },
    4: {
        "query": "How many heads are used in the multi-head attention mechanism of the base Transformer model?",
        "filename": "attention_is_all_you_need.pdf",
        "expected_answer": "The base Transformer model uses 8 attention heads in its multi-head attention mechanism."
    },
    5: {
        "query": "What is Meta Platforms, Inc.'s stock symbol?",
        "filename": "meta_10k.pdf",
        "expected_answer": "Meta Platforms, Inc.'s stock symbol is META."
    },
    6: {
        "query": "As of January 26, 2024, how many shares of Class A common stock did Meta have outstanding?",
        "filename": "meta_10k.pdf",
        "expected_answer": "As of January 26, 2024, Meta had 2,200,048,907 shares of Class A common stock outstanding."
    },
    7: {
        "query": "What is Meta's I.R.S. Employer Identification Number?",
        "filename": "meta_10k.pdf",
        "expected_answer": "Meta's I.R.S. Employer Identification Number is 20-1665019."
    },
    8: {
        "query": "What is the target range for the Operating Surplus Ratio according to Meta's financial indicators?",
        "filename": "meta_10k.pdf",
        "expected_answer": "The target range for the Operating Surplus Ratio is 0%/ - 20%."
    },
    9: {
        "query": "What is the vision for Adelaide according to the strategic plan?",
        "filename": "adelaide_strategic_plan_2024_2028.pdf",
        "expected_answer": "The vision for Adelaide is 'Our Adelaide. Bold. Aspirational. Innovative.'"
    },
    10: {
        "query": "How many residents is Adelaide projected to have by 2036?",
        "filename": "adelaide_strategic_plan_2024_2028.pdf",
        "expected_answer": "Adelaide is projected to have 50,000 residents by 2036."
    },
    11: {
        "query": "What percentage of tree canopy cover is Adelaide aiming to achieve by 2035?",
        "filename": "adelaide_strategic_plan_2024_2028.pdf",
        "expected_answer": "Adelaide is aiming to achieve 40% tree canopy cover by 2035."
    },
    12: {
        "query": "By what year does Adelaide aim to achieve Zero Functional Homelessness?",
        "filename": "adelaide_strategic_plan_2024_2028.pdf",
        "expected_answer": "Adelaide aims to achieve Zero Functional Homelessness by 2026."
    },
    13: {
        "query": "What is the maximum value for the Asset Test Ratio target in Adelaide's financial indicators?",
        "filename": "adelaide_strategic_plan_2024_2028.pdf",
        "expected_answer": "The maximum value for the Asset Test Ratio target is 50%."
    },
    14: {
        "query": "How many attention layers are stacked in both the encoder and decoder of the Transformer model?",
        "filename": "attention_is_all_you_need.pdf",
        "expected_answer": "Both the encoder and decoder of the Transformer model consist of a stack of N = 6 identical layers."
    },
    15: {
        "query": "What is the address of Meta Platforms, Inc.'s principal executive offices?",
        "filename": "meta_10k.pdf",
        "expected_answer": "Meta Platforms, Inc.'s principal executive offices are located at 1 Meta Way, Menlo Park, California 94025."
    },
    16: {
        "query": "What percentage of Adelaide's current residents are aged between 18 and 34?",
        "filename": "adelaide_strategic_plan_2024_2028.pdf",
        "expected_answer": "47%/ of Adelaide's current residents are aged between 18 and 34."
    },
    17: {
        "query": "What is the target for increasing diversion from landfill for residential kerbside waste by 2030?",
        "filename": "adelaide_strategic_plan_2024_2028.pdf",
        "expected_answer": "The target is to increase diversion from landfill for residential kerbside waste from 50% (2020) to 80% by 2030."
    },
    18: {
        "query": "How many parameters does the base Transformer model have?",
        "filename": "attention_is_all_you_need.pdf",
        "expected_answer": "The base Transformer model has 65 million parameters."
    },
    19: {
        "query": "What is the target for the Net Financial Liabilities ratio in Adelaide's financial indicators?",
        "filename": "adelaide_strategic_plan_2024_2028.pdf",
        "expected_answer": "The target for the Net Financial Liabilities ratio is Less than 80%."
    },
    20: {
        "query": "What percentage of Adelaide's current residents are born overseas?",
        "filename": "adelaide_strategic_plan_2024_2028.pdf",
        "expected_answer": "45%/ of Adelaide's current residents are born overseas."
    },
    21: {
        "query": "What programming language did Paul Graham use to write Hacker News?",
        "filename": "paul_graham_essay.txt",
        "expected_answer": "Paul Graham wrote Hacker News in Arc, a new version of Lisp that he and Robert Morris had been working on."
        },
    22: {
        "query": "How many applications did Y Combinator receive for their first Summer Founders Program?",
        "filename": "paul_graham_essay.txt",
        "expected_answer": "Y Combinator received 225 applications for their first Summer Founders Program."
        },
    23: {
        "query": "What was the initial investment deal offered by Y Combinator to startups in their first batch?",
        "filename": "paul_graham_essay.txt",
        "expected_answer": "Y Combinator invested $6k per founder, which was typically $12k for two founders, in return for 6% equity."
        },
    24: {
        "query": "Who suggested to Paul Graham that he should make sure Y Combinator wasn't the last cool thing he did?",
        "filename": "paul_graham_essay.txt",
        "expected_answer": "Robert Morris (Rtm) suggested to Paul Graham that he should make sure Y Combinator wasn't the last cool thing he did."
        },
    25: {
        "query": "What is the name of the new Lisp dialect Paul Graham worked on from 2015 to 2019?",
        "filename": "paul_graham_essay.txt",
        "expected_answer": "The new Lisp dialect Paul Graham worked on from 2015 to 2019 is called Bel."
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
