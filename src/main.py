from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from server import router
from prometheus_fastapi_instrumentator import Instrumentator
from logger import CustomLogger
import uvicorn

logger = CustomLogger.setup_logger(__name__, save_to_disk=True, log_dir='/data/app/logs/main.log')

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
