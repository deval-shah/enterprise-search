import asyncio
import os
import base64
from fastapi import UploadFile
from io import BytesIO
import pytest
import shutil
from llamasearch.api.utils import handle_file_upload, get_file_size_and_partial_md5, get_upload_file_size_and_partial_md5

TEST_FILES = {
    "file1": "./data/test_docs/Adelaide_Strategic_Plan_2024_2028.pdf",
    "file2": "./data/test_docs/university-of-adelaide-enterprise-agreement-2023-2025_0.pdf",
}

UPLOAD_DIR = "./test_uploads"

@pytest.fixture(scope="module")
def event_loop():
    """Provide an event loop for asyncio tests."""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
def upload_dir():
    """Create and manage a temporary upload directory for tests."""
    # Clean up before tests
    if os.path.exists(UPLOAD_DIR):
        shutil.rmtree(UPLOAD_DIR)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    yield UPLOAD_DIR
    # Clean up after tests
    shutil.rmtree(UPLOAD_DIR)

@pytest.mark.asyncio
async def test_handle_file_upload_dict(upload_dir):
    """
    Test file upload functionality using a dictionary input.
    
    This test ensures that files can be uploaded successfully when provided
    as a dictionary with base64 encoded content.
    """
    with open(TEST_FILES["file1"], 'rb') as file:
        file_content = file.read()
    dict_file = [{
        "name": os.path.basename(TEST_FILES["file1"]),
        "content": base64.b64encode(file_content).decode('utf-8')
    }]
    results = await handle_file_upload(dict_file, upload_dir)
    assert len(results) == 1
    assert results[0]["status"] == "success"
    assert os.path.exists(results[0]["location"])

@pytest.mark.asyncio
async def test_handle_file_upload_uploadfile(upload_dir):
    """
    Test file upload functionality using an UploadFile object.

    This test verifies that files can be uploaded successfully when provided
    as FastAPI UploadFile objects.
    """
    with open(TEST_FILES["file2"], 'rb') as file:
        file_content = file.read()
    upload_file = [UploadFile(
        filename=os.path.basename(TEST_FILES["file2"]),
        file=BytesIO(file_content)
    )]
    results = await handle_file_upload(upload_file, upload_dir)
    assert len(results) == 1
    assert results[0]["status"] == "success"
    assert os.path.exists(results[0]["location"])

@pytest.mark.asyncio
async def test_handle_file_upload_existing_file(upload_dir):
    """
    Test file upload functionality when uploading an existing file.

    This test checks the behavior of the upload function when attempting
    to upload a file that already exists in the upload directory.
    """
    with open(TEST_FILES["file1"], 'rb') as file:
        file_content = file.read()
    dict_file = [{
        "name": os.path.basename(TEST_FILES["file1"]),
        "content": base64.b64encode(file_content).decode('utf-8')
    }]
    await handle_file_upload(dict_file, upload_dir)
    results = await handle_file_upload(dict_file, upload_dir)
    assert results[0]["status"] == "success"
    assert "File already exists" in results[0]["info"]

@pytest.mark.asyncio
async def test_handle_file_upload_invalid_input():
    """
    Test file upload functionality with invalid input.

    This test ensures that the upload function raises a ValueError
    when provided with an empty list of files.
    """
    with pytest.raises(ValueError):
        await handle_file_upload([], UPLOAD_DIR)

@pytest.mark.asyncio
async def test_get_file_size_and_partial_md5():
    """
    Test the functionality to get file size and partial MD5 hash.

    This test verifies that the function correctly retrieves the file size
    and calculates a partial MD5 hash for a given file.
    """
    file_path = TEST_FILES["file1"]
    size, md5 = await get_file_size_and_partial_md5(file_path)
    assert size > 0
    assert len(md5) == 32  # MD5 hash is 32 characters long

@pytest.mark.asyncio
async def test_get_upload_file_size_and_partial_md5():
    """
    Test the functionality to get file size and partial MD5 hash for an UploadFile.

    This test ensures that the function correctly calculates the file size
    and partial MD5 hash for a file provided as an UploadFile object.
    """
    with open(TEST_FILES["file1"], 'rb') as file:
        file_content = file.read()
    upload_file = UploadFile(
        filename=os.path.basename(TEST_FILES["file1"]),
        file=BytesIO(file_content)
    )
    size, md5 = await get_upload_file_size_and_partial_md5(upload_file)
    assert size > 0
    assert len(md5) == 32

if __name__ == "__main__":
    pytest.main([__file__])
