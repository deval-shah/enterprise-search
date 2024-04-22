from fastapi import HTTPException, File, UploadFile, Form
from typing import List, Optional
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pipeline import query_app
from logger import CustomLogger
from utils import profile_
from fastapi import APIRouter
import os

class Settings(BaseModel):
    config_path: str = "/app/config/config.yml"
    data_path: str = "/data/files"
    log_dir: str = "/data/app/logs"
    upload_subdir: str = "uploads"

class QueryPayload(BaseModel):
    query: str

settings = Settings()
logger = CustomLogger.setup_logger(__name__, save_to_disk=True, log_dir=settings.log_dir, log_name='server.log')
router = APIRouter()

@profile_
@router.post("/uploadfile/")
async def upload_files(files: List[UploadFile] = File(...)):
    responses = []
    upload_dir = os.path.join(settings.data_path, settings.upload_subdir)
    os.makedirs(upload_dir, exist_ok=True)
    for file in files:
        file_location = os.path.join(upload_dir, file.filename)
        with open(file_location, "wb") as buffer:
            buffer.write(await file.read())
        responses.append(f"File {file.filename} saved at {file_location}")
    return {"files_uploaded": responses}

@profile_
@router.post("/query/", response_model=dict)
async def query_index(query: str = Form(...), files: Optional[List[UploadFile]] = File(None)) -> JSONResponse:
    """
    Processes a query and optionally handles file uploads, then performs a document query.

    Args:
        query (str): The query string to process.
        files (Union[UploadFile, List[UploadFile]], optional): Optional file or files to upload.

    Returns:
        JSONResponse: The query results and file upload status.
    """
    upload_dir = os.path.join(settings.data_path, settings.upload_subdir)
    try:
        file_responses = await upload_files(files) if files else []
        response = await query_app(config_path=settings.config_path, query=query, data_path=upload_dir)
    except HTTPException as e:
        logger.error(f"HTTPException with detail: {e.detail}")
        raise HTTPException(status_code=500, detail=f"An error occurred during processing the query: {query}")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        return JSONResponse(status_code=500, detail=f"An error occurred during processing the query: {query}")
    return JSONResponse(content={"response": response.response, "file_upload": file_responses}, status_code=200)