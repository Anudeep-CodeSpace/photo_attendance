import numpy as np
from typing import List, Dict, Optional
import logging

from insightface.app import FaceAnalysis
from app.config import DETECTOR_MODEL_NAME, DETECTOR_PROVIDER


logger = logging.getLogger("attendance")


class FaceProcessingService:
    """
    Handles face detection using RetinaFace (MobileNet backbone)
    and returns cropped face regions with bounding boxes.
    """

    def __init__(self):
        try:
            logger.info(
                f"Initializing FaceProcessingService with model={DETECTOR_MODEL_NAME}, provider={DETECTOR_PROVIDER}"
            )

            self.detector = FaceAnalysis(
                name=DETECTOR_MODEL_NAME,
                providers=[DETECTOR_PROVIDER],
                allowed_modules=["detection"]
            )
            self.detector.prepare(ctx_id=0, det_size=(640, 640))

            logger.info("Face detector initialized successfully.")

        except Exception as e:
            logger.error(f"Failed to initialize face detector: {str(e)}")
            raise e

    def detect_faces(self, img: np.ndarray) -> List[Dict]:
        """
        Detect all faces in an image and return bounding boxes + crops.
        """
        if img is None:
            logger.warning("detect_faces received None image.")
            return []

        try:
            faces = self.detector.get(img)
        except Exception as e:
            logger.error(f"Face detector inference error: {e}")
            return []

        if not faces:
            logger.info("No faces detected in input image.")
            return []

        detected = []
        h, w = img.shape[:2]

        for face in faces:
            # Convert bbox to safe/clamped coordinates
            try:
                x1, y1, x2, y2 = map(int, face.bbox)
            except Exception as e:
                logger.error(f"Failed reading face bounding box: {e}")
                continue

            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w, x2)
            y2 = min(h, y2)

            if x2 <= x1 or y2 <= y1:
                logger.warning(
                    f"Invalid bounding box detected: "
                    f"({x1}, {y1}, {x2}, {y2})"
                )
                continue

            crop = img[y1:y2, x1:x2]

            detected.append({
                "bbox": [x1, y1, x2, y2],
                "score": float(face.det_score),
                "crop": crop
            })

        return detected

    def detect_single_face(self, img: np.ndarray) -> Optional[np.ndarray]:
        """
        Returns only the highest-confidence face crop.
        """
        faces = self.detect_faces(img)

        if not faces:
            logger.info("detect_single_face: No face found.")
            return None

        best = max(faces, key=lambda f: f["score"])

        # Optional low-score warning
        if best["score"] < 0.4:
            logger.warning(
                f"Low-confidence primary face detected (score={best['score']:.3f})."
            )

        return best["crop"]


# Singleton instance
face_processing_service = FaceProcessingService()
