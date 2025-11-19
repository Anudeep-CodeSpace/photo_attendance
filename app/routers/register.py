from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from fastapi.params import Depends
import asyncio
import cv2
import numpy as np
import logging

from app.locks import registration_lock
from app.dependencies import verify_api_key
from app.services.face_processing import face_processing_service
from app.services.embedding_service import embedding_service
from app.services.sqlite_service import insert_student
from app.services.qdrant_service import upsert_student_embedding
from app.constants.thresholds import RECOGNITION_CONFIDENCE_THRESHOLD
from app.state.progress import progress

router = APIRouter()

logger = logging.getLogger("attendance")


# ----------------------------------------------------------
# Helper: Preprocess ONE student image (parallelizable)
# ----------------------------------------------------------
async def preprocess_student(file: UploadFile):
    filename = file.filename.lower()
    roll_no = filename.rsplit(".", 1)[0].strip()

    if not roll_no:
        logger.warning(f"[{filename}] Invalid filename → cannot extract roll_no")
        return {"file": filename, "roll_no": None, "status": "failed", "reason": "Invalid filename"}

    # Read file
    try:
        raw = await file.read()
    except Exception as e:
        logger.error(f"[{filename}] File read failed: {e}")
        return {"file": filename, "roll_no": roll_no, "status": "failed", "reason": "Read failed"}

    img_array = np.frombuffer(raw, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    if img is None:
        logger.warning(f"[{filename}] Image decode failed.")
        return {"file": filename, "roll_no": roll_no, "status": "failed", "reason": "Decode failed"}

    # Downscale
    max_dim = max(img.shape[:2])
    if max_dim > 1024:
        scale_factor = 1024 / max_dim
        small = cv2.resize(
            img,
            (int(img.shape[1] * scale_factor), int(img.shape[0] * scale_factor)),
            interpolation=cv2.INTER_AREA
        )
    else:
        scale_factor = 1.0
        small = img

    # Detect faces
    detections = await asyncio.to_thread(face_processing_service.detect_faces, small)
    if not detections:
        logger.info(f"[{filename}] No face detected.")
        return {"file": filename, "roll_no": roll_no, "status": "failed", "reason": "No face detected"}

    det = max(detections, key=lambda d: d["score"])
    if det["score"] < RECOGNITION_CONFIDENCE_THRESHOLD:
        logger.warning(
            f"[{filename}] Weak detection score={det['score']:.3f} (threshold={RECOGNITION_CONFIDENCE_THRESHOLD})"
        )
        return {"file": filename, "roll_no": roll_no, "status": "failed", "reason": "Weak detection"}

    # Scale back bbox
    x1, y1, x2, y2 = det["bbox"]
    x1 = int(x1 / scale_factor)
    y1 = int(y1 / scale_factor)
    x2 = int(x2 / scale_factor)
    y2 = int(y2 / scale_factor)

    h, w = img.shape[:2]
    x1 = max(0, min(x1, w - 1))
    x2 = max(0, min(x2, w - 1))
    y1 = max(0, min(y1, h - 1))
    y2 = max(0, min(y2, h - 1))

    if x2 <= x1 or y2 <= y1:
        logger.warning(f"[{filename}] Invalid bounding box after scaling")
        return {"file": filename, "roll_no": roll_no, "status": "failed", "reason": "Invalid bounding box"}

    crop = img[y1:y2, x1:x2]

    # Embedding
    embedding = await asyncio.to_thread(embedding_service.get_embedding, crop)
    if embedding is None:
        logger.error(f"[{filename}] Embedding failed for roll_no={roll_no}")
        return {"file": filename, "roll_no": roll_no, "status": "failed", "reason": "Embedding failed"}

    logger.info(f"[{filename}] Preprocessing OK → ready for DB/Qdrant insert.")

    return {
        "file": filename,
        "roll_no": roll_no,
        "status": "ready",
        "embedding": embedding
    }


# ----------------------------------------------------------
# MAIN ROUTE
# ----------------------------------------------------------
@router.post("/register_students")
async def register_students(files: List[UploadFile] = File(...), authorized: bool = Depends(verify_api_key)):
    logger.info(f"📥 Registration request received with {len(files)} files")

    if len(files) == 0:
        logger.warning("Registration failed: No files uploaded.")
        raise HTTPException(status_code=400, detail="No files uploaded")

    if len(files) > 100:
        logger.warning(f"Registration failed: {len(files)} files uploaded (>100 limit)")
        raise HTTPException(status_code=400, detail="Maximum 100 photos allowed")

    # Acquire lock
    try:
        await asyncio.wait_for(registration_lock.acquire(), timeout=20)
        logger.info("🔒 Lock acquired for registration.")
    except asyncio.TimeoutError:
        logger.warning("Registration blocked: Already in progress.")
        raise HTTPException(status_code=503, detail="Registration in progress")

    # Progress init
    progress["total"] = len(files)
    progress["processed"] = 0
    progress["status"] = "running"
    progress["details"] = []

    try:
        # ------------------------------------------------------
        # 1) Parallel preprocessing
        # ------------------------------------------------------
        logger.info("Starting parallel preprocessing for all images...")
        preprocess_tasks = [preprocess_student(f) for f in files]
        preprocessed = await asyncio.gather(*preprocess_tasks)
        logger.info("Preprocessing complete.")

        # ------------------------------------------------------
        # 2) Sequential DB + Qdrant insert
        # ------------------------------------------------------
        final_results = []
        success_count = 0
        fail_count = 0

        for item in preprocessed:

            # Update progress
            progress["processed"] += 1
            progress["details"].append(item)

            if item["status"] != "ready":
                fail_count += 1
                final_results.append(item)
                logger.info(f"[{item['file']}] Registration skipped: {item['reason']}")
                continue

            roll_no = item["roll_no"]
            embedding = item["embedding"]

            # Insert into SQLite
            inserted = insert_student(roll_no=roll_no)
            if not inserted:
                item["status"] = "failed"
                item["reason"] = "Duplicate"
                fail_count += 1
                logger.warning(f"[{roll_no}] Duplicate roll number. Skipping.")
                final_results.append(item)
                continue

            # Upsert in Qdrant
            await asyncio.to_thread(upsert_student_embedding, roll_no, embedding)

            item["status"] = "success"
            success_count += 1
            final_results.append(item)

            logger.info(f"[{roll_no}] Registration successful.")

        progress["status"] = "done"

        logger.info(
            f"🎉 Registration complete: total={len(files)}, "
            f"success={success_count}, failed={fail_count}"
        )

        return {
            "total_processed": len(files),
            "results": final_results
        }

    except Exception as e:
        progress["status"] = "error"
        logger.error(f"❌ Unexpected registration error: {e}")
        raise e

    finally:
        if registration_lock.locked():
            registration_lock.release()
            logger.info("🔓 Lock released after registration.")
