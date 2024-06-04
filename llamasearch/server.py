from fastapi import HTTPException, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi import APIRouter
from typing import List, Optional
from pipeline import query_app, get_context_from_response
from logger import logger
from utils import profile_
from settings import config
import aiofiles
import os

router = APIRouter()

upload_dir = os.path.join(config.application.data_path, config.application.upload_subdir)

@profile_
@router.post("/uploadfile/")
async def upload_files(files: List[UploadFile] = File(...)):
    try:
        logger.debug(f"Received files: {len(files)}")
        responses = []
        os.makedirs(upload_dir, exist_ok=True)
        logger.debug(f"Upload dir: {upload_dir}, files: {files}")
        for file in files:
            file_location = os.path.join(upload_dir, file.filename)
            async with aiofiles.open(file_location, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)
            responses.append(f"File {file.filename} saved at {file_location}")
        return {"file_upload": responses}
    except HTTPException as e:
        logger.error(f"HTTPException with detail: {e.detail}")
        raise HTTPException(status_code=500, detail=f"An HTTP error occurred while uploading the files to the server {e.detail}")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        return JSONResponse(status_code=500, content={"detail": f"An error occurred while uploading the files to the server: {e.detail}"})

@router.get("/files/")
async def list_files():
    files = os.listdir(upload_dir)
    return JSONResponse(content={"files": files}, status_code=200)

@profile_
@router.post("/query/", response_model=dict)
async def query_index(query: str = Form(...), files: List[UploadFile] = File(None)) -> JSONResponse:
    """
    Processes a query and optionally handles file uploads, then performs a document query.

    Args:
        query (str): The query string to process.
        files (Union[UploadFile, List[UploadFile]], optional): Optional file or files to upload.

    Returns:
        JSONResponse: The query results and file upload status.
    """
    try:
        file_upload_response = []
        if files:
            logger.info(f"Uploading {len(files)} files to the server")
            file_upload_response = await upload_files(files)
            file_upload_response = file_upload_response['file_upload']
        else:
            logger.debug("No files recieved")
        response = await query_app(query=query, data_path=upload_dir)
        logger.debug(f"Raw response from query_app: {response}")
        if response is None or not hasattr(response, 'response'):
            raise ValueError(f"Invalid response from query processing {response}.")
        document_info, retrieval_context = get_context_from_response(response)
        context_details = '\n'.join(["File Path: {}, File Name: {}, Last Modified: {}, Document ID: {}".format(
            path, details['file_name'], details['last_modified_date'], details['doc_id']) for path, details in document_info.items()])
    except HTTPException as e:
        logger.error(f"HTTPException with detail: {e.detail}")
        raise HTTPException(status_code=500, detail=f"An error occurred during processing the query: {query}")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        return JSONResponse(status_code=500, content={"detail": f"An error occurred during processing the query: {query}"})
    return JSONResponse(content={"response": response.response, "context": context_details, "query": query, "file_upload": file_upload_response}, status_code=200)