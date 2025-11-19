from fastapi import Header, HTTPException
import logging
from app.config import ADMIN_API_KEY

logger = logging.getLogger("attendance")

async def verify_api_key(x_api_key: str = Header(None)):
    """
    Verifies the X-API-Key passed in request headers.
    Blocks request if unauthorized.
    """
    if x_api_key is None:
        logger.warning("Missing X-API-Key header.")
        raise HTTPException(status_code=401, detail="API key missing")

    if x_api_key != ADMIN_API_KEY:
        logger.warning("Invalid API key attempted.")
        raise HTTPException(status_code=403, detail="Invalid API key")

    logger.info("API key verified successfully.")
    return True
