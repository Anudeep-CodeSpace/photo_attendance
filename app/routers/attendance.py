from fastapi import APIRouter, UploadFile, File, HTTPException
import cv2
from fastapi.params import Depends
import numpy as np
import asyncio
import logging

from app.dependencies import verify_api_key
from app.constants.thresholds import RECOGNITION_CONFIDENCE_THRESHOLD
from app.locks import registration_lock
from app.services.face_processing import face_processing_service
from app.services.embedding_service import embedding_service
from app.services.qdrant_service import find_best_match

router = APIRouter()

logger = logging.getLogger("attendance")


@router.post("/upload_photo")
async def upload_photo(file: UploadFile = File(...), authorized: bool = Depends(verify_api_key)):
    """
    Accepts one group photo and returns list of recognized roll numbers.
    """
    logger.info(f"📸 Attendance request received: filename={file.filename}")

    # ----------------------------------------
    # Read the uploaded image
    # ----------------------------------------
    raw = await file.read()

    if not raw:
        logger.warning("Empty file uploaded.")
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    img_array = np.frombuffer(raw, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    if img is None:
        logger.error("Failed to decode uploaded image.")
        raise HTTPException(status_code=400, detail="Invalid / unreadable image")

    h, w = img.shape[:2]
    logger.info(f"Image decoded successfully. Resolution={w}x{h}")

    # --------------------------------------
    # Downscale for faster face detection
    # --------------------------------------
    max_dim = max(h, w)
    if max_dim > 1024:
        scale_factor = 1024 / max_dim
        small = cv2.resize(
            img,
            (int(w * scale_factor), int(h * scale_factor)),
            interpolation=cv2.INTER_AREA
        )
        logger.info(f"Downscaled image for detection. Scale factor={scale_factor:.3f}")
    else:
        scale_factor = 1.0
        small = img
        logger.info("Image within optimal size. Skipping downscale.")

    # ----------------------------------------
    # Try acquiring lock (avoid collision with registration)
    # ----------------------------------------
    try:
        await asyncio.wait_for(registration_lock.acquire(), timeout=20)
        logger.info("Lock acquired for attendance processing.")
    except asyncio.TimeoutError:
        logger.warning("Attendance request blocked: registration in progress.")
        raise HTTPException(
            status_code=503,
            detail="System busy with registration. Try again in a few seconds."
        )

    try:
        # ----------------------------------------
        # Detect faces
        # ----------------------------------------
        detections_small = face_processing_service.detect_faces(small)

        if not detections_small:
            logger.info("No faces detected in uploaded photo.")
            return {
                "faces_detected": 0,
                "recognized": []
            }

        logger.info(f"Detected {len(detections_small)} faces (pre-filter).")

        detections = []
        for det in detections_small:

            # Skip low-confidence detections
            if det["score"] < RECOGNITION_CONFIDENCE_THRESHOLD:
                logger.warning(
                    f"Skipped weak detection: score={det['score']:.3f} "
                    f"< threshold={RECOGNITION_CONFIDENCE_THRESHOLD}"
                )
                continue

            # Scale bbox to original coordinates
            x1, y1, x2, y2 = det["bbox"]
            x1 = int(x1 / scale_factor)
            y1 = int(y1 / scale_factor)
            x2 = int(x2 / scale_factor)
            y2 = int(y2 / scale_factor)

            # Clip bbox
            x1 = max(0, min(x1, w - 1))
            y1 = max(0, min(y1, h - 1))
            x2 = max(0, min(x2, w - 1))
            y2 = max(0, min(y2, h - 1))

            if x2 <= x1 or y2 <= y1:
                logger.warning(f"Invalid bbox after scaling: ({x1},{y1}) → ({x2},{y2})")
                continue

            detections.append({
                "bbox": [x1, y1, x2, y2],
                "score": det["score"],
                "crop": img[y1:y2, x1:x2]
            })

        logger.info(f"{len(detections)} faces kept after filtering & bbox cleanup.")

        # ----------------------------------------
        # Parallel embedding + Qdrant search
        # ----------------------------------------
        async def process_face(det):
            crop = det["crop"]

            embedding = await asyncio.to_thread(
                embedding_service.get_embedding,
                crop
            )
            if embedding is None:
                logger.warning("Embedding failed for a detected face.")
                return None

            roll_no = await asyncio.to_thread(find_best_match, embedding)

            if roll_no is None:
                logger.info("Face recognized but below similarity threshold.")
            else:
                logger.info(f"Face recognized as roll_no={roll_no}")

            return {
                "bbox": det["bbox"],
                "score": det["score"],
                "roll_no": roll_no
            }

        tasks = [process_face(det) for det in detections]
        recognized = await asyncio.gather(*tasks)

        recognized = [r for r in recognized if r is not None]

    finally:
        if registration_lock.locked():
            registration_lock.release()
            logger.info("Lock released after attendance processing.")

    # ----------------------------------------
    # Log & return summary
    # ----------------------------------------
    logger.info(
        f"Attendance complete: faces_detected={len(detections)}, "
        f"recognized={sum(1 for r in recognized if r['roll_no'])}"
    )

    return {
        "faces_detected": len(detections),
        "recognized": recognized
    }
