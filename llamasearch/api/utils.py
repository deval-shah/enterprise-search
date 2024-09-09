import asyncio
import os
import hashlib
import aiofiles
from typing import Dict, List, Union
from fastapi import HTTPException
from llamasearch.logger import logger
from llamasearch.settings import config
from starlette.datastructures import UploadFile

CHUNK_SIZE = 64 * 1024  # 64KB chunks
PARTIAL_MD5_SIZE = 8 * 1024  # 8KB for partial MD5

async def handle_file_upload(files: List[Union[UploadFile, Dict[str, Union[str, bytes]]]], user_upload_dir: str) -> List[Dict[str, str]]:
    async def process_file(file: Union[UploadFile, Dict[str, Union[str, bytes]]]):
        try:
            if isinstance(file, UploadFile):
                original_filename = file.filename
            elif isinstance(file, dict):
                original_filename = file['filename']
            else:
                raise ValueError(f"Unsupported file type: {type(file)}")

            file_location = os.path.join(user_upload_dir, original_filename)
            logger.info(f"Uploading file {original_filename} to {file_location}")

            if os.path.exists(file_location):
                existing_size, existing_md5 = await get_file_size_and_partial_md5(file_location)
                new_size, new_md5 = await get_upload_file_size_and_partial_md5(file)
                logger.debug(f"Existing file: size={existing_size}, md5={existing_md5}")
                logger.debug(f"New file: size={new_size}, md5={new_md5}")
                if existing_size == new_size and existing_md5 == new_md5:
                    logger.info(f"File {original_filename} already exists and content is identical")
                    return {
                        "filename": original_filename,
                        "status": "success",
                        "info": "File already exists and content is identical",
                        "location": file_location
                    }
                else:
                    logger.debug(f"File {original_filename} already exists but content is different. "
                                f"Existing size: {existing_size}, New size: {new_size}, "
                                f"Existing MD5: {existing_md5}, New MD5: {new_md5}")
                    base, extension = os.path.splitext(original_filename)
                    counter = 1
                    while os.path.exists(file_location):
                        file_location = os.path.join(user_upload_dir, f"{base}_{counter}{extension}")
                        counter += 1

            if isinstance(file, UploadFile):
                content = await file.read()
                await file.seek(0)
            else:
                content = file['content']

            async with aiofiles.open(file_location, "wb") as file_object:
                await file_object.write(content)

            logger.info(f"File {original_filename} uploaded successfully to {file_location}")
            return {
                "filename": original_filename,
                "status": "success",
                "info": "File uploaded successfully",
                "location": file_location
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