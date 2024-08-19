# query_processor.py
from llamasearch.api.schemas.user import User
from llamasearch.api.core.container import Container
from llamasearch.api.tasks import log_query_task
from llamasearch.pipeline import PipelineFactory
from sqlalchemy.ext.asyncio import AsyncSession
from llamasearch.logger import logger
from llamasearch.api.utils import handle_file_upload
import json
from typing import List, Union
from fastapi import File, UploadFile, Form
import os

async def process_query(
    query: str,
    user: User,
    db: AsyncSession,
    pipeline_factory: PipelineFactory,
    files_: List[str] = None
):
    try:
        pipeline = await pipeline_factory.get_or_create_pipeline_async(user.firebase_uid, user.tenant_id)
        user_upload_dir = pipeline.config.application.data_path
        logger.debug(f"User Upload Dir: {user_upload_dir}")
        files = [UploadFile(filename=file, file=open(os.path.join(user_upload_dir, file), 'rb')) for file in files_] if files_ else []
        file_upload_response = []
        if files:
            logger.info(f"{len(files)} file(s) received")
            upload_results = await handle_file_upload(files, user_upload_dir)
            file_paths = [result['location'] for result in upload_results if result['status'] == "success"]
            logger.info("Inserting file paths : {}".format(file_paths))
            await pipeline.insert_documents(file_paths)
        else:
            logger.info("No files received")

        response = await pipeline.perform_query_async(query)
        logger.debug(f"Raw response from query_app: {response}")

        if response is None or not hasattr(response, 'response'):
            raise ValueError(f"Invalid response from query processing {response}.")

        document_info, retrieval_context = pipeline.get_context_from_response(response)
        context_details = [
            {
                #"file_path": path,
                "file_name": details['file_name'],
                "last_modified": details['last_modified_date'],
                "document_id": details['doc_id']
            }
            for path, details in document_info.items()
        ]
        logger.debug("Context details: " + str(context_details))

        try:
            await log_query_task(db, user.firebase_uid, query, context_details, response.response)
        except Exception as e:
            logger.error(f"Failed to log query for user {user.firebase_uid}: {str(e)}")

        return {
            "response": response.response,
            "context": context_details,
            "query": query,
            "file_upload": file_upload_response
        }

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise