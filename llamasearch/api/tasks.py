# tasks.py
from sqlalchemy.ext.asyncio import AsyncSession
import traceback
from llamasearch.api.db.models import QueryLog
from llamasearch.logger import logger
from typing import Dict, Any

async def log_query_task(db: AsyncSession, firebase_uid: str, query: str, context: Dict[str, Any], response: str):
    try:
        logger.info(f"Attempting to log query for user {firebase_uid}")
        query_log = QueryLog(
            firebase_uid=firebase_uid,
            query=query,
            context=context,
            response=response
        )
        db.add(query_log)
        await db.commit()
        logger.info(f"Query logged successfully for user {firebase_uid}")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error logging query for user {firebase_uid}: {str(e)}")
        logger.exception("Traceback:")
        raise