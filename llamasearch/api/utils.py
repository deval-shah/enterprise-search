import asyncio
import os
import hashlib
import aiofiles
from typing import Dict, List, Union
from fastapi import HTTPException
from llamasearch.logger import logger
from llamasearch.settings import config
from starlette.datastructures import UploadFile
import base64

CHUNK_SIZE = 64 * 1024  # 64KB chunks
PARTIAL_MD5_SIZE = 8 * 1024  # 8KB for partial MD5

async def handle_file_upload(files: List[Union[UploadFile, Dict[str, Union[str, bytes]]]], user_upload_dir: str) -> List[Dict[str, str]]:
    if not files:
        raise ValueError("No files provided for upload")

    async def process_file(file: Union[UploadFile, Dict[str, Union[str, bytes]]]):
        try:
            if isinstance(file, dict):
                original_filename = file.get('name')
                content = base64.b64decode(file.get('content')) if isinstance(file.get('content'), str) else file.get('content')
            elif isinstance(file, UploadFile):
                original_filename = file.filename
                content = await file.read()
            else:
                raise ValueError(f"Unsupported file type: {type(file)}")

            if not content:
                raise ValueError("Invalid file data: empty content")
            if not original_filename:
                raise ValueError("Filename is missing")

            file_location = os.path.join(user_upload_dir, original_filename)
            logger.info(f"Uploading file {original_filename} to {file_location}")

            if os.path.exists(file_location):
                existing_size, existing_md5 = await get_file_size_and_partial_md5(file_location)
                new_size, new_md5 = len(content), hashlib.md5(content).hexdigest()
                if existing_size == new_size and existing_md5 == new_md5:
                    logger.info(f"File {original_filename} already exists and content is identical")
                    return {
                        "filename": original_filename,
                        "status": "success",
                        "info": "File already exists and content is identical",
                        "location": file_location
                    }
                else:
                    logger.info(f"File {original_filename} already exists but content is different")
                    return {
                        "filename": original_filename,
                        "status": "success",
                        "info": "File already exists but content is different",
                        "location": file_location
                    }

            async with aiofiles.open(file_location, "wb") as file_object:
                await file_object.write(content)

            logger.info(f"File {original_filename} uploaded successfully to {file_location}")
            return {
                "filename": original_filename,
                "status": "success",
                "info": "File uploaded successfully",
                "location": file_location
            }
        except ValueError as e:
            logger.error(f"Error processing file {original_filename if 'original_filename' in locals() else 'unknown'}: {str(e)}")
            return {
                "filename": original_filename if 'original_filename' in locals() else "unknown",
                "status": "error",
                "info": str(e),
                "location": None
            }
        except Exception as e:
            logger.error(f"Error uploading file {original_filename if 'original_filename' in locals() else 'unknown'}: {str(e)}")
            return {
                "filename": original_filename if 'original_filename' in locals() else "unknown",
                "status": "error",
                "info": f"Error uploading file: {str(e)}",
                "location": None
            }

    try:
        tasks = [process_file(file) for file in files]
        responses = await asyncio.gather(*tasks)
        return responses
    except Exception as e:
        logger.error(f"Error in file upload process: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred during the file upload process: {str(e)}")

async def handle_chunked_file_upload(chunk_generator, filename, user_upload_dir):
    file_path = os.path.join(user_upload_dir, filename)
    async with aiofiles.open(file_path, 'wb') as f:
        async for chunk in chunk_generator:
            await f.write(chunk)
    return file_path

async def get_file_size_and_partial_md5(file: Union[str, UploadFile, Dict[str, Union[str, bytes]]]) -> tuple:
    if isinstance(file, str):
        file_size = os.path.getsize(file)
        async with aiofiles.open(file, mode='rb') as f:
            content = await f.read()
    elif isinstance(file, UploadFile):
        content = await file.read()
        file_size = len(content)
        await file.seek(0)
    elif isinstance(file, dict):
        content = file['content']
        file_size = len(content)
    else:
        raise ValueError(f"Unsupported file type: {type(file)}")

    md5 = hashlib.md5()
    if file_size <= 2 * PARTIAL_MD5_SIZE:
        md5.update(content)
    else:
        md5.update(content[:PARTIAL_MD5_SIZE])
        md5.update(content[-PARTIAL_MD5_SIZE:])

    return file_size, md5.hexdigest()

async def get_upload_file_size_and_partial_md5(file: Union[UploadFile, Dict[str, Union[str, bytes]]]) -> tuple:
    if isinstance(file, UploadFile):
        content = await file.read()
        await file.seek(0)
    elif isinstance(file, dict):
        content = file['content']
        if isinstance(content, str):
            content = content.encode()
    else:
        raise ValueError(f"Unsupported file type: {type(file)}")

    file_size = len(content)
    md5 = hashlib.md5()

    if file_size <= 2 * PARTIAL_MD5_SIZE:
        md5.update(content)
    else:
        md5.update(content[:PARTIAL_MD5_SIZE])
        md5.update(content[-PARTIAL_MD5_SIZE:])

    return file_size, md5.hexdigest()