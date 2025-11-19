from typing import List, Optional, Any
import numpy as np
import logging

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

from app.config import QDRANT_URL, QDRANT_API_KEY, VECTOR_DIMENSION, QDRANT_COLLECTION_NAME
from app.constants.thresholds import MATCH_THRESHOLD

logger = logging.getLogger("attendance")


# ------------------------------------------------------------
# Initialize client & collection
# ------------------------------------------------------------
def init_qdrant():
    logger.info("Initializing Qdrant client...")

    try:
        client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY
        )
        logger.info(f"Connected to Qdrant at {QDRANT_URL}")

    except Exception as e:
        logger.error(f"Failed to initialize Qdrant client: {e}")
        raise e

    # Check/create collection
    try:
        if not client.collection_exists(QDRANT_COLLECTION_NAME):
            logger.info(f"Qdrant collection '{QDRANT_COLLECTION_NAME}' not found. Creating...")

            client.create_collection(
                collection_name=QDRANT_COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=VECTOR_DIMENSION,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Collection '{QDRANT_COLLECTION_NAME}' created successfully.")
        else:
            logger.info(f"Collection '{QDRANT_COLLECTION_NAME}' already exists.")

    except Exception as e:
        logger.error(f"Failed to create or check Qdrant collection: {e}")
        raise e

    return client


# Global Qdrant client
qdrant_client = init_qdrant()


# ------------------------------------------------------------
# Upsert embedding
# ------------------------------------------------------------
def upsert_student_embedding(
    roll_no: str,
    embedding: np.ndarray,
    payload: Optional[dict] = None
) -> None:
    """
    Inserts or updates a vector embedding for a student.
    """
    if payload is None:
        payload = {"roll_no": roll_no}

    if embedding is None or embedding.ndim != 1:
        logger.error(f"Attempted to upsert invalid embedding for {roll_no}.")
        return

    point = PointStruct(
        id=roll_no,
        vector=embedding.tolist(),
        payload=payload
    )

    try:
        qdrant_client.upsert(
            collection_name=QDRANT_COLLECTION_NAME,
            points=[point]
        )
        logger.info(f"Upserted embedding for roll_no={roll_no}")

    except Exception as e:
        logger.error(f"Failed to upsert embedding for {roll_no}: {e}")


# ------------------------------------------------------------
# Search nearest
# ------------------------------------------------------------
def search_nearest(
    embedding: np.ndarray,
    top_k: int = 1
) -> List[dict]:
    """
    Searches Qdrant for nearest vectors.
    """
    if embedding is None:
        logger.error("search_nearest called with None embedding.")
        return []

    try:
        results = qdrant_client.search(
            collection_name=QDRANT_COLLECTION_NAME,
            query_vector=embedding.tolist(),
            limit=top_k,
            with_payload=True
        )

    except Exception as e:
        logger.error(f"Qdrant search failed: {e}")
        return []

    if not results:
        logger.warning("Qdrant returned no search results.")
        return []

    matches = []
    for hit in results:
        matches.append({
            "roll_no": hit.id,
            "score": hit.score,
            "payload": hit.payload
        })

    return matches


# ------------------------------------------------------------
# Best match finder
# ------------------------------------------------------------
def find_best_match(
    embedding: np.ndarray,
    threshold: float = MATCH_THRESHOLD
) -> Optional[str]:
    """
    Returns roll_no if similarity score exceeds threshold.
    """
    matches = search_nearest(embedding, top_k=1)

    if not matches:
        logger.info("find_best_match: No matches found.")
        return None

    best = matches[0]
    score = best["score"]

    if score >= threshold:
        return best["roll_no"]

    # Log rejected matches (useful for debugging threshold tuning)
    logger.info(
        f"Match found but below threshold: roll_no={best['roll_no']} "
        f"score={score:.4f} < threshold={threshold}"
    )

    return None
