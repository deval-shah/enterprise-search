from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import os
from typing import Optional
import shutil
from pipeline import query_app
from logger import CustomLogger
from utils import profile_endpoint

app = FastAPI()

class Settings(BaseModel):
    config_path: str = "/app/config/config.yml"
    data_path: str = "/data"
    log_dir: str = "/data/app/logs"

settings = Settings()
logger = CustomLogger.setup_logger(__name__, save_to_disk=True, log_dir=settings.log_dir, log_name='server.log')

class QueryPayload(BaseModel):
    query: str

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):
    logger.info("create upload file ")
    file_location = f"{settings.data_path}/{file.filename}"
    try:
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())
        logger.info(f"file '{file.filename}' saved at '{file_location}'")
        return {"info": f"file '{file.filename}' saved at '{file_location}'"}
    except Exception as e:
        logger.error(f"Failed to save file '{file.filename}': {e}")
        raise HTTPException(status_code=500, detail="Failed to save file")

@app.post("/query/", response_model=dict)
@profile_endpoint
async def query_index(query: str = Form(...), file: Optional[UploadFile] = File(None)) -> JSONResponse:
    try:
        if file:
            safe_filename = os.path.basename(file.filename)
            file_path = os.path.join(settings.data_path, safe_filename)
            try:
                logger.info(f"Attempting to save file to {file_path}")
                logger.info(f"Data directory permissions: {os.listdir(settings.data_path)}")
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
            except Exception as e:
                logger.error(f"Error saving file {safe_filename}: {str(e)}")
                raise
            logger.info(f"File {file.filename} saved to {file_path}")
        else:
            logger.info("No file uploaded with the query.")
        response = query_app(config_path=settings.config_path, query=query, data_path=settings.data_path)
    except HTTPException as e:
        logger.error(f"HTTPException: {e.detail}")
        raise HTTPException(status_code=500, detail="An error occurred during processing the query {}.".format(query))
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        return JSONResponse(status_code=500, detail="An error {} occurred during processing the query {}.".format(e.detail, query))
    return JSONResponse(content={"response": response.response}, status_code=200)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
