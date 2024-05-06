from fastapi import HTTPException, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi import APIRouter
from typing import List, Optional
from src.pipeline import query_app
from src.logger import CustomLogger
from src.utils import profile_
from src.settings import config
import os

logger = CustomLogger.setup_logger(__name__, save_to_disk=True, log_dir=config.application.log_dir, log_name='server.log')
router = APIRouter()

upload_dir = os.path.join(config.application.data_path, config.application.upload_subdir)

@profile_
@router.post("/uploadfile/")
async def upload_files(files: List[UploadFile] = File(...)):
    logger.debug(f"Received files: {len(files)}")
    responses = []
    os.makedirs(upload_dir, exist_ok=True)
    logger.debug(f"Upload dir: {upload_dir}, files: {files}")
    for file in files:
        file_location = os.path.join(upload_dir, file.filename)
        with open(file_location, "wb") as buffer:
            buffer.write(await file.read())
        responses.append(f"File {file.filename} saved at {file_location}")
    return JSONResponse(content={"files_uploaded": responses}, status_code=200)

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
        file_responses = None
        if files:
            logger.debug(f"Uploading {len(files)} files to the server")
            file_responses = await upload_files(files)
        else:
            logger.debug("No files recieved")
        response = await query_app(query=query, data_path=upload_dir)
        if response is None or not hasattr(response, 'response'):
            raise ValueError("Invalid response from query processing.")
    except HTTPException as e:
        logger.error(f"HTTPException with detail: {e.detail}")
        raise HTTPException(status_code=500, detail=f"An error occurred during processing the query: {query}")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        return JSONResponse(status_code=500, content={"detail": f"An error occurred during processing the query: {query}"})
    return JSONResponse(content={"response": response.response, "file_upload": file_responses}, status_code=200)