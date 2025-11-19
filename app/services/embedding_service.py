import numpy as np
import cv2
from typing import Optional
from insightface.app import FaceAnalysis

from app.config import EMBEDDING_MODEL_NAME, EMBEDDING_PROVIDER
from app.constants.thresholds import QUALITY_THRESHOLD

import logging
logger = logging.getLogger("attendance")


class EmbeddingService:
    """
    Converts cropped face images into normalized float32 embeddings.
    """

    def __init__(self):
        try:
            logger.info(
                f"Initializing EmbeddingService with model={EMBEDDING_MODEL_NAME}, provider={EMBEDDING_PROVIDER}"
            )
            self.model = FaceAnalysis(
                name=EMBEDDING_MODEL_NAME,
                providers=[EMBEDDING_PROVIDER],
                allowed_modules=["recognition", "detection"]
            )
            self.model.prepare(ctx_id=0)
            logger.info("Embedding model initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {str(e)}")
            raise e

    def get_embedding(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """
        Returns a normalized float32 embedding for the cropped face.
        """
        if face_image is None:
            logger.warning("EmbeddingService received None as face_image.")
            return None

        # Ensure BGR format
        try:
            if face_image.ndim == 3 and face_image.shape[2] == 3:
                face_image = cv2.cvtColor(face_image, cv2.COLOR_RGB2BGR)
        except Exception as e:
            logger.error(f"Error converting image colorspace: {e}")
            return None

        # Run model
        try:
            faces = self.model.get(face_image)
        except Exception as e:
            logger.error(f"Embedding model inference failed: {e}")
            return None

        if not faces:
            logger.info("EmbeddingService: No face detected in crop.")
            return None

        face = max(faces, key=lambda f: f.det_score)

        if face.det_score < QUALITY_THRESHOLD:
            logger.warning(f"Low-quality face detected for embedding (score={face.det_score:.3f}).")

        # Create embedding
        try:
            emb = np.asarray(face.embedding, dtype=np.float32)
        except Exception as e:
            logger.error(f"Failed converting embedding to float32: {e}")
            return None

        # Normalize
        norm = np.linalg.norm(emb)
        if norm == 0 or np.isnan(norm):
            logger.error("Invalid embedding: norm is zero or NaN.")
            return None
        
        emb = emb / norm  # normalize to unit length

        return emb

# Singleton Instance
embedding_service = EmbeddingService()
