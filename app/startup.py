from app.services.face_processing import face_processing_service
from app.services.embedding_service import embedding_service

def prewarm_models():
    """
    Load RetinaFace and InsightFace models into RAM
    before the first request hits.
    """
    try:
        # Run a dummy call on FaceProcessing
        face_processing_service.detector.prepare(ctx_id=0, det_size=(640, 640))

        # Run a dummy call on EmbeddingService
        embedding_service.model.prepare(ctx_id=0, det_size=(224, 224))

        print("[Startup] Models prewarmed successfully.")

    except Exception as e:
        print("[Startup Error] Failed to load models:", str(e))
