from fastapi import FastAPI
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
import uvicorn
from src.logger import logger
from src.server import router

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
