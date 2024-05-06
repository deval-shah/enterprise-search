from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
import uvicorn
from src.logger import CustomLogger
from src.settings import config
from src.server import router

logger = CustomLogger.setup_logger(__name__, save_to_disk=True, log_dir=config.application.log_dir, log_name='server.log')

app = FastAPI()
app.include_router(router)

Instrumentator().instrument(app).expose(app, include_in_schema=True, should_gzip=True)

async def universal_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred."}
    )

app.add_exception_handler(Exception, universal_exception_handler)

if __name__ == "__main__":
    logger.info("Starting FastAPI server.")
    uvicorn.run(app, host="0.0.0.0", port=8000)
