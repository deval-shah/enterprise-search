import asyncio
import os
import hashlib
import aiofiles
from typing import Dict, List
from fastapi import UploadFile, HTTPException
from llamasearch.logger import logger
from llamasearch.settings import config

CHUNK_SIZE = 64 * 1024  # 64KB chunks
PARTIAL_MD5_SIZE = 8 * 1024  # 8KB for partial MD5

async def get_user_upload_dir(user_id: str) -> str:
    upload_dir = os.path.join(config.application.data_path, config.application.upload_subdir)
    user_dir = os.path.join(upload_dir, user_id)
    os.makedirs(user_dir, exist_ok=True)
    logger.info("User upload directory: " + user_dir)
    return user_dir

async def handle_file_upload(files: List[UploadFile], user_id: str) -> List[Dict[str, str]]:
    user_upload_dir = await get_user_upload_dir(user_id)
    responses = []

    async def process_file(file: UploadFile):
        try:
            original_filename = file.filename
            file_location = os.path.join(user_upload_dir, original_filename)
            logger.info(f"Uploading file {original_filename} to {file_location}")
            if os.path.exists(file_location):
                existing_size, existing_md5 = await get_file_size_and_partial_md5(file_location)
                new_size, new_md5 = await get_upload_file_size_and_partial_md5(file)
                
                if existing_size == new_size and existing_md5 == new_md5:
                    logger.info(f"File {original_filename} already exists and content is likely identical")
                    return {
                        "filename": original_filename,
                        "status": "success",
                        "info": "File already exists and content is likely identical",
                        "location": file_location
                    }
                else:
                    logger.info(f"File {original_filename} already exists but content is different")
                    base, extension = os.path.splitext(original_filename)
                    counter = 1
                    while os.path.exists(file_location):
                        file_location = os.path.join(user_upload_dir, f"{base}_{counter}{extension}")
                        counter += 1
            
            async with aiofiles.open(file_location, "wb") as file_object:
                while chunk := await file.read(CHUNK_SIZE):
                    await file_object.write(chunk)
            logger.info(f"File {original_filename} uploaded successfully to {file_location}")
            return {
                "filename": original_filename,
                "status": "success",
                "info": "File uploaded successfully",
                "location": file_location
            }
        except Exception as e:
            logger.error(f"Error uploading file {file.filename}: {str(e)}")
            return {
                "filename": file.filename,
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

async def get_file_size_and_partial_md5(file_path: str) -> tuple:
    file_size = os.path.getsize(file_path)
    async with aiofiles.open(file_path, mode='rb') as f:
        first_chunk = await f.read(PARTIAL_MD5_SIZE)
        await f.seek(-PARTIAL_MD5_SIZE, 2)  # Seek from the end
        last_chunk = await f.read()
    partial_md5 = hashlib.md5(first_chunk + last_chunk).hexdigest()
    return file_size, partial_md5

async def get_upload_file_size_and_partial_md5(file: UploadFile) -> tuple:
    file_size = 0
    md5 = hashlib.md5()
    # Read the first chunk
    first_chunk = await file.read(PARTIAL_MD5_SIZE)
    md5.update(first_chunk)
    file_size += len(first_chunk)
    # Read the rest of the file
    while chunk := await file.read(CHUNK_SIZE):
        file_size += len(chunk)
    # Read the last chunk
    await file.seek(file_size - PARTIAL_MD5_SIZE)
    last_chunk = await file.read()
    md5.update(last_chunk)
    # Reset file pointer
    await file.seek(0)
    return file_size, md5.hexdigest()