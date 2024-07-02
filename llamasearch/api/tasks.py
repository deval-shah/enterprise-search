# tasks.py
from sqlalchemy.orm import Session
import traceback
from llamasearch.api.db.models import QueryLog
from llamasearch.logger import logger

async def log_query_task(db: Session, firebase_uid: str, query: str, context: dict, response: str):
    try:
        logger.info(f"Attempting to log query for user {firebase_uid}")
        query_log = QueryLog(
            firebase_uid=firebase_uid,
            query=query,
            context=context,
            response=response
        )
        db.add(query_log)
        db.commit()
        logger.info(f"Query logged successfully for user {firebase_uid}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error logging query for user {firebase_uid}: {str(e)}")
        logger.error(traceback.format_exc())
        raise