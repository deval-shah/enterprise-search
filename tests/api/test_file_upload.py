import asyncio
import os
import base64
from fastapi import UploadFile
from io import BytesIO
import pytest
from llamasearch.api.utils import handle_file_upload, get_file_size_and_partial_md5, get_upload_file_size_and_partial_md5
from .base_api_test import BaseAPITest

class TestFileUpload(BaseAPITest):
    @pytest.fixture(scope="class")
    def event_loop(self):
        loop = asyncio.get_event_loop()
        yield loop
        loop.close()

    @pytest.mark.asyncio
    async def test_handle_file_upload_dict(self, upload_dir, test_files):
        with open(test_files["file1"], 'rb') as file:
            file_content = file.read()
        dict_file = [{
            "name": os.path.basename(test_files["file1"]),
            "content": base64.b64encode(file_content).decode('utf-8')
        }]
        results = await handle_file_upload(dict_file, upload_dir)
        assert len(results) == 1
        assert results[0]["status"] == "success"
        assert os.path.exists(results[0]["location"])

    @pytest.mark.asyncio
    async def test_handle_file_upload_uploadfile(self, upload_dir, test_files):
        with open(test_files["file2"], 'rb') as file:
            file_content = file.read()
        upload_file = [UploadFile(
            filename=os.path.basename(test_files["file2"]),
            file=BytesIO(file_content)
        )]
        results = await handle_file_upload(upload_file, upload_dir)
        assert len(results) == 1
        assert results[0]["status"] == "success"
        assert os.path.exists(results[0]["location"])

    @pytest.mark.asyncio
    async def test_handle_file_upload_existing_file(self, upload_dir, test_files):
        with open(test_files["file1"], 'rb') as file:
            file_content = file.read()
        dict_file = [{
            "name": os.path.basename(test_files["file1"]),
            "content": base64.b64encode(file_content).decode('utf-8')
        }]
        await handle_file_upload(dict_file, upload_dir)
        results = await handle_file_upload(dict_file, upload_dir)
        assert results[0]["status"] == "success"
        assert "File already exists" in results[0]["info"]

    @pytest.mark.asyncio
    async def test_handle_file_upload_invalid_input(self):
        with pytest.raises(ValueError):
            await handle_file_upload([], "/tmp")

    @pytest.mark.asyncio
    async def test_get_file_size_and_partial_md5(self, test_files):
        file_path = test_files["file1"]
        size, md5 = await get_file_size_and_partial_md5(file_path)
        assert size > 0
        assert len(md5) == 32  # MD5 hash is 32 characters long

    @pytest.mark.asyncio
    async def test_get_upload_file_size_and_partial_md5(self, test_files):
        with open(test_files["file1"], 'rb') as file:
            file_content = file.read()
        upload_file = UploadFile(
            filename=os.path.basename(test_files["file1"]),
            file=BytesIO(file_content)
        )
        size, md5 = await get_upload_file_size_and_partial_md5(upload_file)
        assert size > 0
        assert len(md5) == 32

if __name__ == "__main__":
    pytest.main([__file__])
